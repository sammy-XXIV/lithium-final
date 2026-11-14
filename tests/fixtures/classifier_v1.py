"""Frozen attribution-only extract from 79b1803346416e4a0b5cbd55eb1776653778b0be.
Not used by the production classifier; see attribution-v1-provenance.json."""
import json
from solverline.resolve_fillers import TREASURY, final_result


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
                    if event.get('version') not in {'0.2.0', '0.3.0', '0.4.0', '0.4.1', '0.4.2', '0.4.3'}:
                        malformed = True
                        continue
                    if not isinstance(event.get('data'), list):
                        malformed = True
                        continue
                    for entry in event['data']:
                        if not isinstance(entry, dict):
                            malformed = True
                            continue
                        events.append({'tx_hash': txhash, 'receipt_id': receipt['id'],
                                       'event': event['event'], 'data': entry})
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
    # Deliberately conservative: only a two-account, two-token, exact complementary
    # execution in one receipt. More complex netting stays public but unattributed.
    if len(customers) == 1 and origin != destination:
        customer = customers[0]
        group = [e for e in diffs if (e['tx_hash'], e['receipt_id']) == (customer['tx_hash'], customer['receipt_id'])]
        if len(group) == 2:
            maker = next((e for e in group if e is not customer), None)
            c, m = customer['data'], maker['data']
            try:
                complementary = (set(c['diff']) == set(m['diff']) == {origin, destination}
                                 and all(int(c['diff'][t]) + int(m['diff'][t]) == 0 for t in (origin, destination))
                                 and not any(int(v) for e in group for v in e['data'].get('fees_collected', {}).values()))
            except (ValueError, TypeError, AttributeError):
                complementary = False
            if complementary and m.get('account_id') not in {None, TREASURY, c.get('account_id')}:
                result.update(attribution_status='attributed', filler_account=m['account_id'],
                              reason='unique_exact_complementary_account', evidence=[customer, maker])
    return result


def _positive(value):
    try:
        return int(value) > 0
    except (ValueError, TypeError):
        return False
