"""Keep the documented correction and worked receipt independently replayable."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class AttributionAuditTests(unittest.TestCase):
    def module(self):
        path = ROOT / 'tools/check_attribution_audit.py'
        self.assertTrue(path.exists(), 'Missing historical attribution replay')
        spec = importlib.util.spec_from_file_location('check_attribution_audit', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_same_snapshot_replays_zero_to_current_count_without_network(self):
        with patch('socket.socket.connect', side_effect=AssertionError('audit used network')):
            result = self.module().verify()
        self.assertEqual(result['before_swaps'], 0)
        self.assertEqual(result['after_swaps'], 235)
        self.assertEqual(result['sample_swaps'], 555)

    def test_documented_receipt_table_matches_actual_fixture(self):
        from solverline.analyze import swap_id
        from solverline.resolve_fillers import classify_swap
        module = self.module()
        document = (ROOT / 'docs/ATTRIBUTION_AUDIT.md').read_text(encoding='utf-8')
        table = document.split('<!-- receipt-example:start -->')[1].split('<!-- receipt-example:end -->')[0].strip()
        self.assertEqual(table, module.example_table())
        fixture = json.loads(gzip.decompress((ROOT / 'tests/fixtures/public-fee-netted.json.gz').read_bytes()))
        swap = fixture['swaps'][1]
        result = classify_swap(swap, fixture['transactions'])
        values = [swap_id(swap), swap['createdAt'], swap['intentHashes'], swap['originAsset'], swap['destinationAsset']]
        values += [event[key] for event in result['evidence'] for key in ('tx_hash', 'receipt_id')]
        values += [event['data']['account_id'] for event in result['evidence']]
        for value in values:
            self.assertIn('`' + value + '`', document)

    def test_real_worked_receipt_rejects_changed_delta_and_third_account(self):
        from solverline.resolve_fillers import classify_swap
        fixture = json.loads(gzip.decompress((ROOT / 'tests/fixtures/public-fee-netted.json.gz').read_bytes()))
        swap = fixture['swaps'][1]
        tx_hash = 'Fuq4JhQmzM71kDygLLDSjRNsSxKvqSgr4PRa3Fw3LzUB'
        receipt_id = 'BWMaTNkiqz2sXKmND9M5WuvUv7GtRDJmE665zbQJqG3z'
        for mutation in ('delta', 'third-account'):
            transactions = copy.deepcopy(fixture['transactions'])
            receipt = next(r for r in transactions[tx_hash]['result']['receipts_outcome'] if r['id'] == receipt_id)
            events = [(i, json.loads(log[11:])) for i, log in enumerate(receipt['outcome']['logs'])
                      if log.startswith('EVENT_JSON:')]
            index, event = next((i, e) for i, e in events if e['event'] == 'token_diff')
            if mutation == 'delta':
                token = swap['originAsset']
                event['data'][0]['diff'][token] = str(int(event['data'][0]['diff'][token]) + 1)
            else:
                entry = copy.deepcopy(event['data'][0])
                entry['account_id'] = 'third-account.near'
                event['data'].append(entry)
            receipt['outcome']['logs'][index] = 'EVENT_JSON:' + json.dumps(event)
            with self.subTest(mutation=mutation):
                self.assertIsNone(classify_swap(swap, transactions)['filler_account'])


if __name__ == '__main__':
    unittest.main()
