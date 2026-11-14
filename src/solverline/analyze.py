"""Decimal USD coverage, conservative account-concentration bounds and CSV evidence."""
import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, localcontext, ROUND_FLOOR, ROUND_CEILING
from pathlib import Path

from .pull_explorer import ROOT
from .resolve_fillers import write_json

ZERO = Decimal(0)
CLASSES = ('public', 'confidential_treasury', 'unresolved')


def money(value):
    try:
        amount = Decimal(str(value))
        return amount if amount.is_finite() and amount >= 0 else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def text(value):
    if value is None:
        return None
    formatted = format(value, 'f')
    return formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted


def ratio(numerator, denominator):
    return text(numerator / denominator) if denominator else None


def concentration(account_volumes, unknown):
    volumes = sorted((Decimal(v) for v in account_volumes), reverse=True)
    unknown = Decimal(unknown)
    if any(not v.is_finite() or v < 0 for v in [*volumes, unknown]):
        raise ValueError('Concentration volumes must be finite and nonnegative')
    with localcontext() as context:
        context.prec = 50
        known = sum(volumes, ZERO)
        total = known + unknown
        squares = sum((v * v for v in volumes), ZERO)
        largest = volumes[0] if volumes else ZERO
        result = {'subset_hhi': ratio(squares, known * known)}
        for n in (1, 3, 10):
            top = sum(volumes[:n], ZERO)
            result[f'subset_top{n}'] = ratio(top, known)
            context.rounding = ROUND_FLOOR
            result[f'top{n}_lower'] = ratio(top, total)
            context.rounding = ROUND_CEILING
            result[f'top{n}_upper'] = ratio(min(total, top + unknown), total)
        context.rounding = ROUND_FLOOR
        result['hhi_lower'] = ratio(squares, total * total)
        context.rounding = ROUND_CEILING
        result['hhi_upper'] = ratio((largest + unknown) ** 2 + squares - largest ** 2, total * total)
        return result


def one_swap_one_filler_scenario(rows, accounts, total):
    """Conditional bounds if each unattributed Explorer swap is one indivisible fill."""
    known_accounts = [Decimal(v) for v in accounts.values()]
    unknown_swaps, known_swap_count = [], 0
    for row in rows:
        value = money(row.get('amountInUsd'))
        if value is None:
            continue
        if (row.get('filler_account') and row.get('attribution_status') == 'attributed'
                and row.get('settlement_class') == 'public'):
            known_swap_count += 1
        else:
            unknown_swaps.append(value)
    result = {'one_swap_one_filler_assumed_fill_count': known_swap_count + len(unknown_swaps)}
    if not total:
        result.update({f'one_swap_one_filler_top{n}_{bound}': None
                       for n in (1, 3, 10) for bound in ('lower', 'upper')})
        result.update(one_swap_one_filler_hhi_lower=None, one_swap_one_filler_hhi_upper=None)
        return result
    lower_accounts = sorted([*known_accounts, *unknown_swaps], reverse=True)
    outer = concentration(accounts.values(), total - sum(accounts.values(), ZERO))
    with localcontext() as context:
        context.prec = 50
        for n in (1, 3, 10):
            result[f'one_swap_one_filler_top{n}_lower'] = ratio(sum(lower_accounts[:n], ZERO), total)
            result[f'one_swap_one_filler_top{n}_upper'] = outer[f'top{n}_upper']
        result['one_swap_one_filler_hhi_lower'] = ratio(sum((v * v for v in lower_accounts), ZERO), total * total)
        result['one_swap_one_filler_hhi_upper'] = outer['hhi_upper']
    return result


def aggregate(rows):
    classes = dict.fromkeys(CLASSES, ZERO)
    accounts = defaultdict(lambda: ZERO)
    total = known = complete_usd = ZERO
    invalid = valid = complete_count = 0
    for row in rows:
        value = money(row.get('amountInUsd'))
        if value is None:
            invalid += 1
            continue
        category = row['settlement_class']
        if category not in CLASSES:
            raise ValueError('Unknown settlement class')
        total += value
        classes[category] += value
        valid += 1
        if row.get('rpc_complete'):
            complete_count += 1
            complete_usd += value
        filler = row.get('filler_account')
        if filler and row.get('attribution_status') == 'attributed' and category == 'public':
            known += value
            accounts[filler] += value
    result = {'count': len(rows), 'valid_usd_count': valid, 'invalid_usd_count': invalid,
              'total_usd': text(total), 'attributable_usd': text(known), 'unknown_usd': text(total - known),
              'attributable_share': ratio(known, total), 'rpc_complete_count': complete_count,
              'rpc_complete_usd_share': ratio(complete_usd, total),
              'attributed_account_count': len(accounts)}
    for category, volume in classes.items():
        result[f'{category}_usd'] = text(volume)
        result[f'{category}_share'] = ratio(volume, total)
    result.update(concentration(accounts.values(), total - known))
    result.update(one_swap_one_filler_scenario(rows, accounts, total))
    return result


def size_bin(value):
    if value is None:
        return 'invalid USD'
    return '[0,100)' if value < 100 else '[100,1000)' if value < 1000 else '[1000,infinity)'


def swap_id(row):
    identity = [row['depositAddress'], row.get('depositMemo') or None]
    return hashlib.sha256(json.dumps(identity, separators=(',', ':')).encode()).hexdigest()[:24]


def write_csv(path, rows, fields=None):
    rows = list(rows)
    fields = fields or (list(rows[0]) if rows else ['label', 'count', 'usd', 'share'])
    with Path(path).open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def analyze(rows, manifest, directory=None, *, identity=swap_id):
    from .sensitivity import sensitivity
    directory = Path(directory or ROOT / 'data/derived')
    directory.mkdir(parents=True, exist_ok=True)
    summary = aggregate(rows)
    summary.update(tx_total=manifest['tx_total'], tx_available=manifest['tx_available'],
                   receipt_run_complete=manifest['receipt_run_complete'],
                   provider_refused=manifest.get('provider_refused', False),
                   windows=len(manifest['windows']), bigquery=manifest['bigquery'])
    groupings = {'date': lambda r: r['sample_window'][:10],
                 'slot': lambda r: r['sample_window'][11:16],
                 'window': lambda r: r['sample_window'],
                 'pair': lambda r: r['originAsset'] + ' → ' + r['destinationAsset'],
                 'size': lambda r: size_bin(money(r.get('amountInUsd'))),
                 'date_pair_size': lambda r: json.dumps([r['sample_window'][:10], r['originAsset'],
                                                       r['destinationAsset'], size_bin(money(r.get('amountInUsd')))], separators=(',', ':'))}
    breakdowns = {}
    for name, get_label in groupings.items():
        groups = defaultdict(list)
        if name in ('date', 'slot', 'window'):
            for window in manifest['windows']:
                label = window['start'][:10] if name == 'date' else window['start'][11:16] if name == 'slot' else window['start']
                groups[label] = []
        elif name == 'size':
            for label in ('[0,100)', '[100,1000)', '[1000,infinity)'):
                groups[label] = []
        for row in rows:
            groups[get_label(row)].append(row)
        breakdowns[name] = [{'label': label, **aggregate(group)} for label, group in sorted(groups.items())]
        write_csv(directory / f'coverage-{name}.csv', breakdowns[name])
    refs, fees, accounts = defaultdict(lambda: [0, ZERO]), defaultdict(lambda: [0, ZERO]), defaultdict(lambda: ZERO)
    shipped, evidence = [], []
    for row in rows:
        value = money(row.get('amountInUsd'))
        if value is not None:
            referral = row.get('referral') or '(missing referral)'
            refs[referral][0] += 1
            refs[referral][1] += value
            recipients = {f['recipient'] for f in row.get('appFees', []) if f.get('recipient')}
            for recipient in recipients:
                fees[recipient][0] += 1
                fees[recipient][1] += value
            if row.get('filler_account') and row.get('attribution_status') == 'attributed':
                accounts[row['filler_account']] += value
        row_identity = identity(row)
        shipped.append({'swap_id': row_identity, 'created_at': row['createdAt'], 'window': row['sample_window'],
                        'origin_asset': row['originAsset'], 'destination_asset': row['destinationAsset'],
                        'size_bin': size_bin(value), 'input_usd': text(value), 'settlement_class': row['settlement_class'],
                        'attribution_status': row['attribution_status'], 'filler_account': row['filler_account'],
                        'rpc_complete': str(row['rpc_complete']).lower(), 'tx_count': row['tx_count'],
                        'tx_available': row['tx_available'], 'reason': row['reason'],
                        'referral': row.get('referral'), 'fee_recipients': json.dumps(sorted({f['recipient'] for f in row.get('appFees', []) if f.get('recipient')})),
                        'near_tx_hashes': json.dumps(row.get('nearTxHashes', [])), 'source_file': row['source_file']})
        evidence.append({'swap_id': row_identity, 'settlement_class': row['settlement_class'], 'reason': row['reason'],
                         'intent_hashes': row.get('intentHashes'), 'near_tx_hashes': row.get('nearTxHashes', []),
                         'events': row['evidence']})
    distributions = {}
    for name, values in (('referrals', refs), ('fee-recipients', fees)):
        distributions[name] = [{'label': label, 'count': count, 'usd': text(usd),
                                 'share': ratio(usd, Decimal(summary['total_usd']))}
                                for label, (count, usd) in sorted(values.items(), key=lambda v: (-v[1][1], v[0]))]
        write_csv(directory / f'{name}.csv', distributions[name])
    account_rows = [{'account': account, 'usd': text(usd)} for account, usd in sorted(accounts.items())]
    write_csv(directory / 'accounts.csv', account_rows, ['account', 'usd'])
    write_csv(directory / 'swaps.csv', shipped)
    write_json(directory / 'evidence.json', evidence)
    write_json(directory / 'summary.json', summary)
    write_json(directory / 'manifest.json', manifest)
    checks = sensitivity(rows, identity=identity)
    write_json(directory / 'sensitivity.json', checks)
    write_csv(directory / 'sensitivity.csv', checks['scenarios'])
    write_csv(directory / 'account-persistence.csv', checks['accounts'],
              ['account', 'swap_count', 'observed_dates', 'observed_windows', 'input_usd',
               'share_of_all_usd', 'largest_swap_share_of_account_usd'])
    return {'summary': summary, 'breakdowns': breakdowns, 'distributions': distributions, 'accounts': account_rows}


if __name__ == '__main__':
    directory = ROOT / 'data/derived'
    report = analyze(json.loads((directory / 'classified.json').read_text()),
                     json.loads((directory / 'manifest.json').read_text()))
    print(json.dumps(report['summary'], indent=2))
