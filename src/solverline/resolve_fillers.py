"""Conservative receipt classification and resumable, throttled archival RPC cache."""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from email.utils import parsedate_to_datetime
from email.message import Message
from pathlib import Path

from .pull_explorer import ROOT, key
from .bigquery import load_inventory, inventory_status

TREASURY = '51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe'
ARCHIVAL_RPC = 'https://archival-rpc.mainnet.near.org'
RPC_DIR = ROOT / 'data/raw/rpc'
SCHEMA_VERSION = 2


def configured_rpc():
    if os.environ.get('SOLVERLINE_RPC_URL'):
        return os.environ['SOLVERLINE_RPC_URL']
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text().splitlines():
            name, separator, value = line.partition('=')
            if separator and name.strip() == 'ARCHIVAL_RPC_URL' and value.strip():
                return value.strip()
    return ARCHIVAL_RPC


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def load_windows(config=ROOT / 'sampling.json', directory=None):
    directory = Path(directory or ROOT / 'data/raw/explorer')
    config = Path(config)
    cfg = json.loads(config.read_text())
    fingerprint = hashlib.sha256(config.read_bytes()).hexdigest()
    stored = directory / '_config.sha256'
    if stored.exists() and stored.read_text().strip() != fingerprint:
        raise ValueError('sampling config differs from cached Explorer config')
    rows, windows, seen = [], [], {}
    for date in cfg['dates']:
        for slot in cfg['slots_utc']:
            start = dt.datetime.fromisoformat(f'{date}T{slot}:00+00:00')
            end = start + dt.timedelta(minutes=cfg['window_minutes'])
            path = directory / f'{start:%Y%m%dT%H%M}.json'
            if not path.exists():
                raise FileNotFoundError(f'Missing Explorer window: {path.name}; fetch explicit scope first')
            body = json.loads(path.read_text())
            parse = lambda text: dt.datetime.fromisoformat(text.replace('Z', '+00:00'))
            if parse(body['start']) != start or parse(body['end']) != end:
                raise ValueError(f'Cached window scope differs: {path.name}')
            if not body.get('complete') or body['count'] != len(body['swaps']):
                raise ValueError(f'Incomplete Explorer window: {path.name}')
            windows.append({'file': path.name, 'start': body['start'], 'end': body['end'],
                            'count': body['count'], 'complete': True, 'fetched_at': body.get('fetched_at'),
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            for swap in body['swaps']:
                if swap.get('status') != 'SUCCESS' or not start <= parse(swap['createdAt']) < end:
                    raise ValueError(f'Invalid record in {path.name}')
                identity = key(swap)
                if identity in seen:
                    if seen[identity] != swap:
                        raise ValueError('Conflicting duplicate Explorer swap')
                    continue
                seen[identity] = swap
                rows.append({**swap, 'sample_window': body['start'], 'source_file': path.name})
    return rows, {'config_sha256': fingerprint, 'windows': windows, 'schema_version': SCHEMA_VERSION,
                  'sampling': {name: cfg[name] for name in ('dates', 'slots_utc', 'window_minutes', 'statuses', 'page_size')}}


def final_result(data, txhash):
    result = data.get('result', {}) if isinstance(data, dict) else {}
    status = result.get('status', {})
    if (result.get('transaction', {}).get('hash') != txhash
            or result.get('final_execution_status') != 'FINAL'
            or not isinstance(result.get('receipts_outcome'), list)
            or not ('SuccessValue' in status or 'Failure' in status)):
        return None
    outcomes = [result.get('transaction_outcome', {})] + result['receipts_outcome']
    try:
        by_id = {outcome['id']: outcome['outcome'] for outcome in outcomes}
        if len(by_id) != len(outcomes) or outcomes[0]['id'] != txhash:
            return None
        visited, pending = set(), [txhash]
        while pending:
            identity = pending.pop()
            if identity in visited:
                continue
            outcome = by_id[identity]
            if not any(key in outcome['status'] for key in ('SuccessValue', 'SuccessReceiptId', 'Failure')):
                return None
            visited.add(identity)
            pending.extend(outcome['receipt_ids'])
        if visited == set(by_id):
            return result
    except (KeyError, TypeError):
        pass
    return None


class RpcCache:
    def __init__(self, directory=RPC_DIR, endpoint=ARCHIVAL_RPC, interval=5.2, tries=3, request_timeout=30):
        self.directory = Path(directory)
        self.endpoint, self.interval, self.tries = endpoint, interval, tries
        self.last_start = 0.0
        self.errors = {}
        self.provider_refused = False
        self.request_timeout = request_timeout

    def path(self, txhash):
        if not re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]{1,88}', txhash):
            raise ValueError('Invalid transaction hash')
        return self.directory / f'{txhash}.json'

    def read(self, txhash):
        path = self.path(txhash)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
        except (ValueError, OSError):
            return None
        if not data.get('_meta', {}).get('endpoint'):
            return None
        return data if final_result(data, txhash) else None

    def _request(self, txhash):
        # OS curl provides a total wall-time deadline, including DNS and slow body
        # streams. A Python socket timeout alone only bounds individual operations.
        executable = shutil.which('curl.exe' if os.name == 'nt' else 'curl')
        if not executable:
            raise RuntimeError('curl is required for bounded RPC fetches; offline rebuilds do not require it')
        payload = json.dumps({'jsonrpc': '2.0', 'id': 'solverline', 'method': 'EXPERIMENTAL_tx_status',
                              'params': [txhash, 'intents.near']})
        with tempfile.TemporaryDirectory(prefix='solverline-rpc-') as tmp:
            body, headers = Path(tmp) / 'body', Path(tmp) / 'headers'
            try:
                response = subprocess.run([executable, '--silent', '--show-error',
                    '--connect-timeout', str(min(10, self.request_timeout)),
                    '--max-time', str(self.request_timeout), '--header', 'Content-Type: application/json',
                    '--user-agent', 'Solverline-research/1.0', '--data-binary', payload,
                    '--dump-header', str(headers), '--output', str(body), '--write-out', '%{http_code}',
                    self.endpoint], capture_output=True, text=True, timeout=self.request_timeout + 2)
            except subprocess.TimeoutExpired:
                raise urllib.error.URLError('RPC transport deadline exceeded') from None
            if response.returncode:
                raise urllib.error.URLError('RPC transport failed or timed out')
            code = int(response.stdout)
            if code >= 400:
                parsed = Message()
                for line in headers.read_text().splitlines():
                    name, separator, value = line.partition(':')
                    if separator and name.lower() == 'retry-after':
                        parsed['Retry-After'] = value.strip()
                raise urllib.error.HTTPError(self.endpoint, code, 'RPC request failed', parsed, None)
            return json.loads(body.read_text(encoding='utf-8'))

    def fetch(self, txhash):
        cached = self.read(txhash)
        if cached:
            return cached
        for attempt in range(self.tries):
            time.sleep(max(0, self.interval - (time.monotonic() - self.last_start)))
            self.last_start = time.monotonic()
            delay = min(60, 5 * (2 ** attempt))
            try:
                data = self._request(txhash)
                error = data.get('error', {})
                if error.get('code') == -429 and 'deprecated' in str(error.get('message', '')).lower():
                    self.provider_refused = True
                    self.errors[txhash] = 'provider_refused_deprecated_endpoint'
                    return None
                if final_result(data, txhash):
                    write_json(self.path(txhash), {**data, '_meta': {'endpoint': self.endpoint,
                               'fetched_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                               'response_sha256': hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()}})
                    self.errors.pop(txhash, None)
                    return self.read(txhash)
                reason = 'rpc_error_or_nonfinal_response'
            except urllib.error.HTTPError as exc:
                reason = f'http_{exc.code}'
                retry = exc.headers.get('Retry-After') if exc.headers else None
                if retry:
                    try:
                        delay = max(delay, float(retry))
                    except ValueError:
                        try:
                            delay = max(delay, parsedate_to_datetime(retry).timestamp() - time.time())
                        except (ValueError, TypeError):
                            pass
            except (urllib.error.URLError, TimeoutError, OSError, ValueError):
                reason = 'network_or_response_error'
            self.errors[txhash] = reason
            if attempt + 1 < self.tries:
                time.sleep(delay)
        return None


def classify_swap(swap, transactions):
    hashes = list(dict.fromkeys(swap.get('nearTxHashes') or []))
    result = {'settlement_class': 'unresolved', 'attribution_status': 'unattributed',
              'filler_account': None, 'reason': 'no_linked_settlement', 'evidence': [],
              'rpc_complete': bool(hashes), 'tx_count': len(hashes), 'tx_available': 0}
    events, malformed = [], False
    for txhash in hashes:
        raw = transactions.get(txhash)
        tx = final_result(raw, txhash) if raw else None
        if not tx:
            result['rpc_complete'] = False
            continue
        result['tx_available'] += 1
        if 'Failure' in tx['status']:
            result['rpc_complete'] = False
            continue
        for receipt in tx['receipts_outcome']:
            outcome = receipt.get('outcome', {})
            if outcome.get('executor_id') != 'intents.near' or 'SuccessValue' not in outcome.get('status', {}):
                continue
            for log in outcome.get('logs', []):
                if not log.startswith('EVENT_JSON:'):
                    continue
                try:
                    event = json.loads(log[len('EVENT_JSON:'):])
                    if event.get('standard') != 'dip4':
                        continue
                    supported = event.get('version') in {'0.2.0', '0.3.0', '0.4.0', '0.4.1', '0.4.2', '0.4.3'}
                    # Older contracts version this event separately from token_diff.
                    supported |= event.get('version') == '0.3.1' and event.get('event') == 'intents_executed'
                    if not supported:
                        malformed = True
                        continue
                    if not isinstance(event.get('data'), list):
                        malformed = True
                        continue
                    for entry in event['data']:
                        if not isinstance(entry, dict):
                            malformed = True
                            continue
                        if event.get('event') == 'token_diff' and (
                                not isinstance(entry.get('diff'), dict) or not entry['diff']
                                or not isinstance(entry.get('account_id'), str) or not entry['account_id']
                                or ('intent_hash' in entry and not isinstance(entry['intent_hash'], str))):
                            malformed = True
                            continue
                        events.append({'tx_hash': txhash, 'receipt_id': receipt['id'],
                                       'version': event['version'], 'event': event['event'], 'data': entry})
                except (ValueError, KeyError, TypeError):
                    malformed = True
    intent_hashes = swap.get('intentHashes') or []
    intent_hashes = set(intent_hashes.split(',') if isinstance(intent_hashes, str) else intent_hashes)
    anchors = {e['data']['account_id'] for e in events
               if e['data'].get('intent_hash') in intent_hashes and e['data'].get('account_id')}
    anchors.discard(TREASURY)
    origin, destination = swap.get('originAsset'), swap.get('destinationAsset')
    transfers = [e for e in events if e['event'] == 'transfer' and isinstance(e['data'].get('tokens'), dict)]
    if not result['rpc_complete'] or malformed:
        result['reason'] = 'missing_or_failed_rpc' if not result['rpc_complete'] else 'unsupported_event_schema'
        return result
    for account in sorted(anchors):
        shield = [e for e in transfers if e['data'].get('account_id') == account
                  and e['data'].get('receiver_id') == TREASURY and _positive(e['data']['tokens'].get(origin))]
        release = [e for e in transfers if e['data'].get('account_id') == TREASURY
                   and e['data'].get('receiver_id') == account and _positive(e['data']['tokens'].get(destination))]
        if shield and release:
            result.update(settlement_class='confidential_treasury', reason='linked_treasury_shield_and_release',
                          evidence=[shield[0], release[0]])
            return result
    diffs = [e for e in events if e['event'] == 'token_diff' and isinstance(e['data'].get('diff'), dict)]
    customers = []
    for event in diffs:
        data = event['data']
        if data.get('account_id') in anchors and data.get('intent_hash') in intent_hashes:
            try:
                if int(data['diff'].get(origin, 0)) < 0 < int(data['diff'].get(destination, 0)):
                    customers.append(event)
            except (ValueError, TypeError):
                continue
    if not customers:
        return result
    result.update(settlement_class='public', reason='ambiguous_public_execution', evidence=customers)
    # More than one receipt or customer account prevents unique attribution.
    if (origin != destination and len({(e['tx_hash'], e['receipt_id']) for e in customers}) == 1
            and len({e['data']['account_id'] for e in customers}) == 1):
        customer = customers[0]
        group = [e for e in diffs if (e['tx_hash'], e['receipt_id']) == (customer['tx_hash'], customer['receipt_id'])]
        account = customer['data']['account_id']
        # Check every customer token_diff across all linked transactions, not only
        # the subset with the main asset pair or a convenient matching hash.
        customer_entries = [e for e in diffs if e['data'].get('account_id') == account]
        if all(e in group and e['data'].get('intent_hash') in intent_hashes for e in customer_entries):
            maker = fee_netted_counterparty(group, account, origin, destination)
            if maker:
                result.update(attribution_status='attributed', filler_account=maker,
                              reason='unique_fee_balanced_counterparty', evidence=group)
    return result


def fee_netted_counterparty(group, customer, origin, destination):
    """Identify an executing account only in a closed two-account token_diff batch.

    This does not identify an independent operator. NEP245 transfer edges are not
    used: the contract constructs those by matching net deltas, not signed pairs.
    """
    def integer(value):
        if isinstance(value, bool) or not isinstance(value, (str, int)) or not re.fullmatch(r'-?[0-9]+', str(value)):
            raise ValueError('Non-integer event amount')
        return int(value)
    try:
        accounts = {e['data']['account_id'] for e in group}
        if (len(accounts) != 2 or customer not in accounts or TREASURY in accounts
                or any(not isinstance(a, str) or not a for a in accounts)):
            return None
        maker = next(iter(accounts - {customer}))
        totals = {account: {} for account in accounts}
        fees = {}
        for event in group:
            data = event['data']
            if not isinstance(data.get('intent_hash'), str) or not data['intent_hash']:
                return None
            delta = {token: integer(value) for token, value in data['diff'].items()}
            for token, value in delta.items():
                totals[data['account_id']][token] = totals[data['account_id']].get(token, 0) + value
            for token, value in data.get('fees_collected', {}).items():
                amount = integer(value)
                if amount < 0 or (amount > 0 and (delta.get(token, 0) >= 0 or amount > -delta[token])):
                    return None
                fees[token] = fees.get(token, 0) + amount
        c, m = totals[customer], totals[maker]
        tokens = c.keys() | m.keys() | fees.keys()
        if any(c.get(t, 0) + m.get(t, 0) + fees.get(t, 0) != 0 for t in tokens):
            return None
        if c.get(origin, 0) < 0 < m.get(origin, 0) and m.get(destination, 0) < 0 < c.get(destination, 0):
            return maker
    except (ValueError, TypeError, KeyError, AttributeError):
        pass
    return None


def _positive(value):
    try:
        return int(value) > 0
    except (ValueError, TypeError):
        return False


def resolve(config=ROOT / 'sampling.json', fetch=False, endpoint=None, explorer_directory=None, derived_directory=None,
            rpc_directory=None):
    swaps, manifest = load_windows(config, explorer_directory)
    hashes = sorted({h for row in swaps for h in row.get('nearTxHashes', [])})
    rpc_directory = Path(rpc_directory or RPC_DIR)
    cache = RpcCache(directory=rpc_directory, endpoint=endpoint or configured_rpc())
    endpoint_hash = hashlib.sha256(cache.endpoint.encode()).hexdigest()
    progress_file = rpc_directory / '_progress.json'
    if not fetch and progress_file.exists():
        previous = json.loads(progress_file.read_text())
        if previous.get('endpoint_sha256') == endpoint_hash:
            cache.provider_refused = previous.get('provider_refused', False)
            cache.errors = previous.get('errors', {})
    transactions = {h: cached for h in hashes if (cached := cache.read(h)) is not None}
    for index, txhash in enumerate(hashes, 1):
        data = cache.fetch(txhash) if fetch else cache.read(txhash)
        if data:
            transactions[txhash] = data
        if fetch:
            write_json(progress_file, {'checked': index, 'total': len(hashes),
                       'available': len(transactions), 'errors': cache.errors,
                       'provider_refused': cache.provider_refused,
                       'endpoint_sha256': endpoint_hash,
                       'updated_at': dt.datetime.now(dt.timezone.utc).isoformat()})
            if index % 10 == 0 or index == len(hashes) or cache.provider_refused:
                print(f'RPC {index}/{len(hashes)} checked; {len(transactions)} available; {len(cache.errors)} errors', flush=True)
            if cache.provider_refused:
                print('Provider explicitly refused the deprecated endpoint. Collection stopped; cached results preserved.', flush=True)
                break
    classified = [{**swap, **classify_swap(swap, transactions)} for swap in swaps]
    provider = urlsplit(cache.endpoint)
    public_endpoint = f'{provider.scheme}://{provider.hostname}'
    manifest.update(tx_total=len(hashes), tx_available=len(transactions), rpc_endpoint=public_endpoint,
                    rpc_endpoint_sha256=endpoint_hash,
                    provider_refused=cache.provider_refused,
                    rpc_errors=cache.errors, receipt_run_complete=len(transactions) == len(hashes),
                    bigquery=inventory_status(load_inventory()),
                    rpc_sha256={h: hashlib.sha256(cache.path(h).read_bytes()).hexdigest() for h in transactions})
    manifest['rpc_sources'] = sorted({f'{urlsplit(data["_meta"]["endpoint"]).scheme}://{urlsplit(data["_meta"]["endpoint"]).hostname}' for data in transactions.values()})
    destination = Path(derived_directory or ROOT / 'data/derived')
    write_json(destination / 'classified.json', classified)
    write_json(destination / 'manifest.json', manifest)
    return classified, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'sampling.json')
    parser.add_argument('--fetch', action='store_true', help='Fetch missing archival receipts; ~2h for 1333 hashes')
    args = parser.parse_args()
    rows, manifest = resolve(args.config, args.fetch)
    print(f'{len(rows)} swaps classified; {manifest["tx_available"]}/{manifest["tx_total"]} transaction results available')


if __name__ == '__main__':
    main()
