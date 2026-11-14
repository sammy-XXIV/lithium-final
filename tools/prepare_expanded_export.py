"""Prepare a bounded warehouse export and public Explorer-only cohort manifest."""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from solverline.resolve_fillers import load_windows, write_json
from solverline.analyze import money, text, swap_id
from solverline.pull_explorer import key


def prepare():
    config = ROOT / 'sampling-expanded.json'
    rows, manifest = load_windows(config, ROOT / 'data/raw/explorer-expanded')
    baseline, baseline_manifest = load_windows()
    indexed = {key(row): row for row in rows}
    core = ('amountInUsd', 'originAsset', 'destinationAsset', 'intentHashes', 'nearTxHashes')
    baseline_preserved = all(key(row) in indexed and all(row.get(k) == indexed[key(row)].get(k) for k in core) for row in baseline)
    if not baseline_preserved:
        raise ValueError('Expanded cohort does not preserve the original baseline core records')
    hashes = sorted({h for row in rows for h in row.get('nearTxHashes', [])})
    if not all(re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]{32,88}', value) for value in hashes):
        raise ValueError('Unexpected transaction hash shape')
    wanted = ',\n'.join("'" + h + "'" for h in hashes)
    # A broad bounded range permits cross-chain settlement after swap creation.
    first = (dt.date.fromisoformat(manifest['sampling']['dates'][0]) - dt.timedelta(days=1)).isoformat()
    last = dt.datetime.now(dt.timezone.utc).date().isoformat()
    sql = f"""-- Expanded cohort execution evidence. Execution status is recorded in job metadata.
-- Raw warehouse records retain their actual fields/statuses; no synthetic RPC finality.
-- Window sample and requested hashes are frozen in the expanded Explorer manifest.
WITH wanted AS (
  SELECT transaction_hash FROM UNNEST([
{wanted}
  ]) AS transaction_hash
), origins AS (
  SELECT DISTINCT receipt_id, originated_from_transaction_hash AS transaction_hash
  FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_origin_transaction`
  WHERE block_date BETWEEN DATE '{first}' AND DATE '{last}'
    AND originated_from_transaction_hash IN (SELECT transaction_hash FROM wanted)
)
SELECT 'transaction' AS record_type, t.transaction_hash, TO_JSON_STRING(t) AS record_json
FROM `bigquery-public-data.crypto_near_mainnet_us.transactions` AS t
JOIN wanted USING (transaction_hash)
WHERE t.block_date BETWEEN DATE '{first}' AND DATE '{last}'
UNION ALL
SELECT 'outcome' AS record_type, o.transaction_hash, TO_JSON_STRING(e) AS record_json
FROM `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` AS e
JOIN origins AS o USING (receipt_id)
WHERE e.block_date BETWEEN DATE '{first}' AND DATE '{last}';
"""
    if len(sql.encode()) >= 1024 * 1024:
        raise ValueError('Prepared query exceeds unresolved query size budget')
    output = ROOT / 'queries/03_expanded_execution_export.sql'
    output.write_text(sql, encoding='utf-8', newline='\n')
    values = [money(row.get('amountInUsd')) for row in rows]
    total = sum((v for v in values if v is not None), money(0))
    public = ROOT / 'docs/data'
    with (public / 'expanded-swaps.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['swap_id','created_at','window','input_usd','origin_asset','destination_asset','intent_hashes','near_tx_hashes'])
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(swap_id=swap_id(row), created_at=row['createdAt'], window=row['sample_window'],
                        input_usd=text(money(row.get('amountInUsd'))), origin_asset=row['originAsset'],
                        destination_asset=row['destinationAsset'], intent_hashes=json.dumps(row.get('intentHashes')),
                        near_tx_hashes=json.dumps(row.get('nearTxHashes', []))))
    write_json(public / 'expanded-cohort.json', dict(status='explorer_complete_execution_resolution_pending',
               count=len(rows), total_usd=text(total), invalid_usd_count=sum(v is None for v in values),
               linked_hashes=len(hashes), minutes=len(manifest['windows']) * manifest['sampling']['window_minutes'],
               sampling=manifest['sampling'], config_sha256=manifest['config_sha256'], windows=manifest['windows'],
               baseline_comparison=dict(count=len(baseline), core_records_preserved=baseline_preserved,
                                        config_sha256=baseline_manifest['config_sha256']),
               prepared_sql_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
               csv_sha256=hashlib.sha256((public / 'expanded-swaps.csv').read_bytes()).hexdigest(),
               warning='Explorer collection only. No expanded attribution, receipt completeness or warehouse execution is claimed.'))
    print(f'Prepared {len(rows)} swaps / {len(hashes)} hashes; {output.stat().st_size} SQL bytes. No warehouse query executed.')


if __name__ == '__main__':
    prepare()
