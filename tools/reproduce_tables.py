"""Offline analytical build from docs/data. No snapshot, credentials or packages needed."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from solverline.analyze import analyze
from solverline.bigquery import STEM, load_inventory, inventory_status
from solverline.build_dashboard import build_dashboard


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def published_rows(data):
    evidence_list = read_json(data / 'evidence.json')
    evidence = {row['swap_id']: row for row in evidence_list}
    if len(evidence) != len(evidence_list):
        raise ValueError('Duplicate evidence swap IDs')
    with (data / 'swaps.csv').open(encoding='utf-8', newline='') as handle:
        shipped = list(csv.DictReader(handle))
    ids = [row['swap_id'] for row in shipped]
    if len(set(ids)) != len(ids) or set(ids) != set(evidence):
        raise ValueError('Swap/evidence identity inventory mismatch')
    rows = []
    for row in shipped:
        proof = evidence[row['swap_id']]
        hashes = json.loads(row['near_tx_hashes'])
        if (proof['near_tx_hashes'] != hashes or proof['reason'] != row['reason']
                or proof['settlement_class'] != row['settlement_class']):
            raise ValueError('Swap/evidence linkage mismatch: ' + row['swap_id'])
        if row['rpc_complete'] not in ('true', 'false'):
            raise ValueError('Invalid receipt-completeness flag')
        rows.append(dict(published_swap_id=row['swap_id'], createdAt=row['created_at'],
                         sample_window=row['window'], originAsset=row['origin_asset'],
                         destinationAsset=row['destination_asset'], amountInUsd=row['input_usd'] or None,
                         settlement_class=row['settlement_class'], attribution_status=row['attribution_status'],
                         filler_account=row['filler_account'] or None, rpc_complete=row['rpc_complete'] == 'true',
                         tx_count=int(row['tx_count']), tx_available=int(row['tx_available']),
                         reason=row['reason'], referral=row['referral'] or None,
                         appFees=[{'recipient': r} for r in json.loads(row['fee_recipients'])],
                         nearTxHashes=hashes, intentHashes=proof['intent_hashes'],
                         source_file=row['source_file'], evidence=proof['events']))
    return rows


def reproduce(data, output):
    data, output = Path(data).resolve(), Path(output).resolve()
    # A verification command must never overwrite the inputs or source checkout.
    if output == data.parent or output in data.parents or output.is_relative_to(data.parent):
        raise ValueError('Output must be outside the published docs directory')
    if output == ROOT or output in ROOT.parents or output.is_relative_to(ROOT / 'src'):
        raise ValueError('Output must not overwrite the source checkout')
    with tempfile.TemporaryDirectory() as temporary:
        scratch = Path(temporary)
        # Restore original names solely to reuse the existing hash-checked inventory reader.
        queries = scratch / 'queries'
        for original, target in [('query.sql', f'{STEM}.sql'),
                                 ('results.json', f'results/{STEM}.json'),
                                 ('job.json', f'results/{STEM}.job.json'),
                                 ('provenance.json', f'results/{STEM}.provenance.json')]:
            destination = queries / target
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(data / 'bigquery' / original, destination)
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('Offline build attempted network')):
            inventory = load_inventory(queries)
            manifest = read_json(data / 'manifest.json')
            if manifest['bigquery'] != inventory_status(inventory):
                raise ValueError('Warehouse inventory disagrees with manifest')
            report = analyze(published_rows(data), manifest, directory=scratch / 'derived',
                             identity=lambda row: row['published_swap_id'])
            build_dashboard(report, derived=scratch / 'derived', docs=output,
                            inventory=inventory, economic=read_json(data / 'economic-baseline.json'))
        for name in ('SPIKE_RESULT.md', 'ATTRIBUTION_AUDIT.md'):
            shutil.copyfile(data.parent / name, output / name)
        expected, actual = read_json(data / 'summary.json'), report['summary']
        differences = sorted(key for key in expected.keys() | actual.keys() if expected.get(key) != actual.get(key))
        success = not differences
        print(('FAIL' if differences else 'PASS') + ' summary.json' + (': ' + ', '.join(differences) if differences else ' (every field)'))
        for path in sorted(p for p in output.rglob('*') if p.is_file()):
            relative = path.relative_to(output)
            original = data.parent / relative
            # Normalize transport line endings; preserve every other byte.
            matches = original.is_file() and path.read_bytes().replace(b'\r\n', b'\n') == original.read_bytes().replace(b'\r\n', b'\n')
            print(('PASS ' if matches else 'FAIL ') + relative.as_posix())
            success &= matches
    print(('PASS' if success else 'FAIL') + ': published analytical tables, charts and presentation; classifications are inputs, not reauthenticated here.')
    return success


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT / 'docs/data')
    parser.add_argument('--output', type=Path, default=ROOT / 'reproduced/from-data')
    args = parser.parse_args()
    try:
        return 0 if reproduce(args.data, args.output) else 1
    except (OSError, ValueError, KeyError, AssertionError) as error:
        print(f'FAIL: {error}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
