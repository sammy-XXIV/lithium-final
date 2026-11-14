"""Catch false solver attribution and caching failed RPC responses."""
import copy
import gzip
import http.server
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def receipt(entries, status=None, executor='intents.near'):
    return {'id': 'receipt', 'outcome': {'executor_id': executor,
            'receipt_ids': [],
            'status': status or {'SuccessValue': ''},
            'logs': ['EVENT_JSON:' + json.dumps({'standard': 'dip4', 'version': '0.4.3',
                                                'event': kind, 'data': data}) for kind, data in entries]}}


def transaction(outcomes, txhash='tx'):
    return {'result': {'final_execution_status': 'FINAL',
                       'transaction_outcome': {'id': txhash, 'outcome': {'receipt_ids': [r['id'] for r in outcomes], 'status': {'SuccessValue': ''}}},
                       'transaction': {'hash': txhash, 'signer_id': 'relayer.near'},
                       'status': {'SuccessValue': ''}, 'receipts_outcome': outcomes}}


class ResolverTests(unittest.TestCase):
    def test_fee_netted_multi_intent_execution_requires_closed_two_account_batch(self):
        from solverline.resolve_fillers import classify_swap, TREASURY
        swap = {'nearTxHashes': ['tx'], 'intentHashes': 'customer-hash', 'originAsset': 'A', 'destinationAsset': 'B'}
        entries = [
            {'account_id': 'customer', 'intent_hash': 'customer-hash', 'diff': {'A': '-101', 'B': '90'}, 'fees_collected': {'A': '1'}},
            {'account_id': 'maker', 'intent_hash': 'maker-1', 'diff': {'A': '100', 'C': '-51'}, 'fees_collected': {'C': '1'}},
            {'account_id': 'maker', 'intent_hash': 'maker-2', 'diff': {'C': '50', 'B': '-91'}, 'fees_collected': {'B': '1'}}]
        data = transaction([receipt([('token_diff', entries)])])
        result = classify_swap(swap, {'tx': data})
        self.assertEqual(result['filler_account'], 'maker')
        self.assertEqual(len(result['evidence']), 3)
        for change in ['third-account', 'unbalanced', 'treasury', 'unlinked-customer', 'invalid-fee', 'float-delta', 'malformed-third-account']:
            broken = copy.deepcopy(entries)
            if change == 'third-account': broken[2]['account_id'] = 'other-maker'
            if change == 'unbalanced': broken[2]['diff']['C'] = '49'
            if change == 'treasury':
                for entry in broken[1:]: entry['account_id'] = TREASURY
            if change == 'unlinked-customer': broken.append({'account_id': 'customer', 'intent_hash': 'different', 'diff': {'A': '0'}})
            if change == 'invalid-fee': broken[0]['fees_collected']['B'] = '-1'
            if change == 'float-delta': broken[0]['diff']['A'] = -101.9
            if change == 'malformed-third-account': broken.append({'account_id': 'other-maker', 'intent_hash': 'third', 'diff': 'unsupported'})
            with self.subTest(change=change):
                self.assertIsNone(classify_swap(swap, {'tx': transaction([receipt([('token_diff', broken)])])})['filler_account'])
        extra = receipt([('token_diff', [{'account_id': 'customer', 'intent_hash': 'customer-hash', 'diff': {'C': '1'}}])])
        extra['id'] = 'another-execution'
        self.assertIsNone(classify_swap(swap, {'tx': transaction([receipt([('token_diff', entries)]), extra])})['filler_account'])

    def test_observed_intents_executed_031_does_not_poison_known_token_diff(self):
        from solverline.resolve_fillers import classify_swap
        swap = {'nearTxHashes': ['tx'], 'intentHashes': 'user-hash', 'originAsset': 'A', 'destinationAsset': 'B'}
        entries = [{'account_id': 'user', 'intent_hash': 'user-hash', 'diff': {'A': '-100', 'B': '90'}},
                   {'account_id': 'maker', 'intent_hash': 'maker-hash', 'diff': {'A': '100', 'B': '-90'}}]
        r = receipt([('token_diff', entries)])
        r['outcome']['logs'].append('EVENT_JSON:' + json.dumps({'standard': 'dip4', 'version': '0.3.1',
            'event': 'intents_executed', 'data': [{'account_id': 'user', 'intent_hash': 'user-hash', 'nonce': 'public-nonce'}]}))
        self.assertEqual(classify_swap(swap, {'tx': transaction([r])})['filler_account'], 'maker')

    @classmethod
    def setUpClass(cls):
        cls.spike = json.loads(gzip.decompress((ROOT / 'tests/fixtures/spike.json.gz').read_bytes()))

    def test_unrelated_execution_for_same_account_does_not_attribute(self):
        from solverline.resolve_fillers import classify_swap
        swap = {'nearTxHashes': ['tx'], 'intentHashes': 'linked', 'originAsset': 'A', 'destinationAsset': 'B'}
        linked = receipt([('intents_executed', [{'account_id': 'user', 'intent_hash': 'linked'}])])
        linked['id'] = 'linked-receipt'
        unrelated = receipt([('token_diff', [
            {'account_id': 'user', 'intent_hash': 'other', 'diff': {'A': '-100', 'B': '90'}},
            {'account_id': 'wrong-maker', 'intent_hash': 'maker', 'diff': {'A': '100', 'B': '-90'}}])])
        result = classify_swap(swap, {'tx': transaction([linked, unrelated])})
        self.assertIsNone(result['filler_account'])

    def test_missing_referenced_receipt_stays_unresolved_and_retryable(self):
        from solverline.resolve_fillers import classify_swap, final_result
        swap = self.spike['swaps'][0]
        txs = copy.deepcopy(self.spike['transactions'])
        first = swap['nearTxHashes'][0]
        txs[first]['result']['receipts_outcome'].pop(0)
        self.assertTrue(final_result(txs[first], first) is None)
        result = classify_swap(swap, txs)
        self.assertFalse(result['rpc_complete'])
        self.assertEqual(result['settlement_class'], 'unresolved')

    def test_explicit_provider_refusal_stops_further_collection(self):
        from solverline.resolve_fillers import RpcCache
        with tempfile.TemporaryDirectory() as tmp:
            cache = RpcCache(Path(tmp), interval=0, tries=1)
            with patch.object(cache, '_request', return_value={'error': {'code': -429, 'message': 'THIS ENDPOINT IS DEPRECATED'}}):
                self.assertIsNone(cache.fetch('tx'))
            self.assertTrue(cache.provider_refused)
            self.assertFalse((Path(tmp) / 'tx.json').exists())

    def test_rpc_transport_caches_a_real_http_response(self):
        from solverline.resolve_fillers import RpcCache
        response = transaction([])
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if request.get('method') != 'EXPERIMENTAL_tx_status' or request.get('params') != ['tx', 'intents.near']:
                    self.send_error(400)
                    return
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                cache = RpcCache(Path(tmp), endpoint=f'http://127.0.0.1:{server.server_port}', interval=0, tries=1)
                self.assertIsNotNone(cache.fetch('tx'))
                self.assertTrue((Path(tmp) / 'tx.json').exists())
        finally:
            server.shutdown()
            server.server_close()

    def test_slow_response_cannot_keep_a_request_alive_indefinitely(self):
        from solverline.resolve_fillers import RpcCache
        class SlowHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200)
                self.end_headers()
                try:
                    self.wfile.write(b'{')
                    for _ in range(30):
                        self.wfile.write(b' ')
                        self.wfile.flush()
                        time.sleep(.06)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass
            def log_message(self, *args):
                pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), SlowHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                cache = RpcCache(Path(tmp), endpoint=f'http://127.0.0.1:{server.server_port}',
                                 interval=0, tries=1, request_timeout=.15)
                started = time.monotonic()
                self.assertIsNone(cache.fetch('tx'))
                self.assertLess(time.monotonic() - started, 1)
        finally:
            server.shutdown()
            server.server_close()

    def test_original_five_are_confidential_without_fillers(self):
        from solverline.resolve_fillers import classify_swap
        swaps = self.spike['swaps']
        for swap in swaps:
            txs = self.spike['transactions']
            with self.subTest(created=swap['createdAt']):
                result = classify_swap(swap, txs)
                self.assertEqual(result['settlement_class'], 'confidential_treasury')
                self.assertIsNone(result['filler_account'])
                self.assertTrue(result['rpc_complete'])
                self.assertGreaterEqual(len(result['evidence']), 2)

    def test_real_fee_netted_public_receipts_identify_executing_accounts(self):
        from solverline.resolve_fillers import classify_swap, final_result
        fixture = json.loads(gzip.decompress((ROOT / 'tests/fixtures/public-fee-netted.json.gz').read_bytes()))
        for txhash, response in fixture['transactions'].items():
            self.assertIsNotNone(final_result(response, txhash))
        for swap, account in zip(fixture['swaps'], fixture['expected_accounts']):
            with self.subTest(created=swap['createdAt']):
                result = classify_swap(swap, fixture['transactions'])
                self.assertEqual(result['settlement_class'], 'public')
                self.assertEqual(result['filler_account'], account)
                self.assertEqual(result['reason'], 'unique_fee_balanced_counterparty')

    def test_unique_public_complement_requires_link_and_success(self):
        from solverline.resolve_fillers import classify_swap
        swap = {'nearTxHashes': ['tx'], 'intentHashes': 'user-hash', 'originAsset': 'A', 'destinationAsset': 'B'}
        entries = [{'account_id': 'user.near', 'intent_hash': 'user-hash', 'diff': {'A': '-100', 'B': '90'}},
                   {'account_id': 'maker.near', 'intent_hash': 'maker-hash', 'diff': {'A': '100', 'B': '-90'}}]
        data = transaction([receipt([('token_diff', entries)])])
        result = classify_swap(swap, {'tx': data})
        self.assertEqual((result['settlement_class'], result['filler_account']), ('public', 'maker.near'))
        failed = copy.deepcopy(data)
        failed['result']['receipts_outcome'][0]['outcome']['status'] = {'Failure': {'error': 'failed'}}
        self.assertEqual(classify_swap(swap, {'tx': failed})['settlement_class'], 'unresolved')
        result = classify_swap({**swap, 'intentHashes': 'unrelated'}, {'tx': data})
        self.assertEqual(result['settlement_class'], 'unresolved')

    def test_unrelated_treasury_and_ambiguous_public_are_not_fillers(self):
        from solverline.resolve_fillers import TREASURY, classify_swap
        swap = {'nearTxHashes': ['tx'], 'intentHashes': 'u', 'originAsset': 'A', 'destinationAsset': 'B'}
        unrelated = [('transfer', [{'account_id': 'unrelated', 'receiver_id': TREASURY, 'tokens': {'A': '100'}}])]
        self.assertEqual(classify_swap(swap, {'tx': transaction([receipt(unrelated)])})['settlement_class'], 'unresolved')
        entries = [{'account_id': 'user', 'intent_hash': 'u', 'diff': {'A': '-100', 'B': '90'}},
                   {'account_id': 'm1', 'diff': {'A': '50', 'B': '-45'}},
                   {'account_id': 'm2', 'diff': {'A': '50', 'B': '-45'}}]
        result = classify_swap(swap, {'tx': transaction([receipt([('token_diff', entries)])])})
        self.assertEqual(result['settlement_class'], 'public')
        self.assertIsNone(result['filler_account'])
        result = classify_swap({**swap, 'nearTxHashes': ['tx', 'missing']}, {'tx': transaction([receipt([('token_diff', entries)])])})
        self.assertFalse(result['rpc_complete'])
        self.assertIsNone(result['filler_account'])

    def test_rpc_error_is_retryable_and_success_is_resumable(self):
        from solverline.resolve_fillers import RpcCache
        with tempfile.TemporaryDirectory() as tmp:
            cache = RpcCache(Path(tmp), interval=0, tries=1)
            with patch.object(cache, '_request', return_value={'error': {'message': 'temporary'}}):
                self.assertIsNone(cache.fetch('tx'))
            self.assertFalse((Path(tmp) / 'tx.json').exists())
            with patch.object(cache, '_request', return_value=transaction([])):
                self.assertIsNotNone(cache.fetch('tx'))
            with patch.object(cache, '_request', side_effect=AssertionError('cached fetch used network')):
                self.assertIsNotNone(cache.fetch('tx'))


if __name__ == '__main__':
    unittest.main()
