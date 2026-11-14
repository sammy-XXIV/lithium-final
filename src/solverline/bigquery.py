"""Render the imported, hash-checked warehouse inventory without network access."""
import csv
import hashlib
import html
import json
import shutil
from collections import Counter
from pathlib import Path

from .pull_explorer import ROOT

STEM = '02_sample_window_event_inventory'


def load_inventory(source=None):
    source = Path(source or ROOT / 'queries')
    results = source / 'results'
    if not (results / f'{STEM}.provenance.json').exists():
        return None
    provenance = json.loads((results / f'{STEM}.provenance.json').read_text(encoding='utf-8'))
    for name, expected in provenance['files'].items():
        path = source / Path(name).relative_to('queries')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'BigQuery evidence hash mismatch: {name}')
    rows = json.loads((results / f'{STEM}.json').read_text(encoding='utf-8'))
    job = json.loads((results / f'{STEM}.job.json').read_text(encoding='utf-8'))
    if job['status']['state'] != 'DONE' or job['status'].get('errorResult'):
        raise ValueError('BigQuery job did not complete successfully')
    totals, windows = Counter(), {}
    for row in rows:
        status, count = row['status'], int(row['event_log_count'])
        if count < 0 or not 0 <= int(row['receipts_with_event']) <= count:
            raise ValueError('Invalid BigQuery event counts')
        totals[status] += count
        key = (row['observed_date'], int(row['utc_hour']))
        window = windows.setdefault(key, dict(date=key[0], utc_hour=key[1], SUCCESS_VALUE=0,
                                             FAILURE=0, SUCCESS_RECEIPT_ID=0,
                                             intents_executed=0, token_diff=0))
        if status not in ('SUCCESS_VALUE', 'FAILURE', 'SUCCESS_RECEIPT_ID'):
            raise ValueError(f'Unreviewed execution status: {status}')
        window[status] += count
        if status == 'SUCCESS_VALUE' and row['event_name'] in ('intents_executed', 'token_diff'):
            window[row['event_name']] += count
    return dict(rows=rows, job=job, totals=dict(totals), windows=[windows[k] for k in sorted(windows)],
                source=source, provenance=provenance)


def inventory_status(evidence):
    if evidence is None:
        return dict(status='incomplete', reason='No imported warehouse event inventory')
    return dict(status='executed_event_inventory', job_id=evidence['job']['jobReference']['jobId'],
                windows_with_events=len(evidence['windows']),
                scope='Verifier event counts only; no swap-level reconciliation or solver attribution')


def render_inventory(evidence, docs):
    if evidence is None:
        return '<section id="bigquery"><h2>BigQuery evidence</h2><p>Incomplete: no imported warehouse event inventory.</p></section>'
    destination = docs / 'data/bigquery'
    destination.mkdir(parents=True, exist_ok=True)
    source = evidence['source']
    for original, name in [(source / f'{STEM}.sql', 'query.sql'),
                           (source / 'results' / f'{STEM}.json', 'results.json'),
                           (source / 'results' / f'{STEM}.job.json', 'job.json'),
                           (source / 'results' / f'{STEM}.provenance.json', 'provenance.json')]:
        shutil.copyfile(original, destination / name)
    windows, totals = evidence['windows'], evidence['totals']
    with (destination / 'windows.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(windows[0]))
        writer.writeheader()
        writer.writerows(windows)
    by_date = Counter()
    for window in windows:
        by_date[window['date']] += window['intents_executed']
    maximum = max(by_date.values(), default=1) or 1
    chart = ''.join(f'<div class="bar-row"><div class="bar-label"><span>{date}</span>'
                    f'<span>{count:,} event logs</span></div><div class="track">'
                    f'<div class="fill" style="width:{count / maximum * 100:.4f}%"></div></div></div>'
                    for date, count in sorted(by_date.items()))
    body = ''.join('<tr><td>' + w['date'] + f' {w["utc_hour"]:02}:00</td>' +
                   ''.join(f'<td class="num">{w[k]:,}</td>' for k in
                           ('SUCCESS_VALUE', 'FAILURE', 'SUCCESS_RECEIPT_ID', 'intents_executed', 'token_diff')) + '</tr>'
                   for w in windows)
    stats = evidence['job']['statistics']['query']
    job_id = html.escape(evidence['job']['jobReference']['jobId'])
    sql = html.escape((source / f'{STEM}.sql').read_text(encoding='utf-8'))
    return f'''<section id="bigquery"><div class="section-head"><h2>A warehouse check of public activity</h2><span class="tag">Executed BigQuery SQL</span></div>
<p>NEAR's public warehouse returned event groups in all {len(windows)} original baseline two-minute windows. These are verifier event logs, not swaps or identified solvers. The SQL covers all <code>intents.near</code> activity in the baseline windows; it has not been joined to the 555 Explorer swaps.</p>
<div class="stats"><div class="stat"><strong>{totals['SUCCESS_VALUE']:,}</strong><span>Event logs on SUCCESS_VALUE outcomes</span></div><div class="stat"><strong>{totals['FAILURE']:,}</strong><span>Event logs on FAILURE outcomes</span></div><div class="stat"><strong>{totals['SUCCESS_RECEIPT_ID']:,}</strong><span>Event logs on SUCCESS_RECEIPT_ID outcomes</span></div></div>
<h3>Successful intents_executed event logs</h3><p class="caption"><strong>Shows:</strong> absolute successful event-log counts across three two-minute UTC windows per date, scaled to the largest sampled date. <strong>Does not show:</strong> swap count, USD volume, solver identities or full indexing coverage.</p>{chart}
<details><summary>Exact counts in all 24 windows</summary><div class="table-wrap"><table><thead><tr><th>UTC window start</th><th class="num">SUCCESS_VALUE logs</th><th class="num">FAILURE logs</th><th class="num">SUCCESS_RECEIPT_ID logs</th><th class="num">intents_executed success logs</th><th class="num">token_diff success logs</th></tr></thead><tbody>{body}</tbody></table></div></details>
<p class="caption">FAILURE logs do not establish completed transfers. SUCCESS_RECEIPT_ID can indicate a continuation; downstream completion is not checked here. Group-specific distinct receipt counts in the raw results overlap across event types and must not be summed as unique receipts. Results in a window do not prove full indexing. The warehouse audit leaves the existing USD coverage and attribution bounds unchanged.</p>
<div class="downloads"><a href="data/bigquery/windows.csv" download>Window counts CSV</a><a href="data/bigquery/results.json">Raw query results</a><a href="data/bigquery/job.json">Job metadata (identity fields removed)</a><a href="data/bigquery/provenance.json">Import hashes</a><a href="data/bigquery/query.sql" download>Executed SQL</a></div>
<details><summary>Executed query and scan budget</summary><p>Job <code>{job_id}</code> · us-east1 · cache hit: {str(stats['cacheHit']).lower()} · {int(stats['totalBytesProcessed']):,} bytes processed · {int(stats['totalBytesBilled']):,} bytes billed · {stats['totalPartitionsProcessed']} daily partitions · 16 GiB cap.</p><p>Executed in the user's authenticated Cloud Shell; original downloaded files imported locally with SHA-256 hashes. The query was dry-run before execution. Its date predicate prunes eight partitions; timestamp fields select 48 minutes within them.</p><pre>{sql}</pre></details></section>'''
