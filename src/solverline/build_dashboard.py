"""Build a static, auditable coverage dashboard with locally shipped assets."""
import csv
import datetime as dt
import html
import json
import shutil
from pathlib import Path
from urllib.parse import urlencode, quote

from .pull_explorer import ROOT
from .resolve_fillers import write_json
from .bigquery import load_inventory, render_inventory
from .sensitivity import investment_brief
from .durability import make_inputs as durability_inputs, render as durability_panel

ASSETS = Path(__file__).with_name('assets')
COLORS = {'public': '#17647b', 'confidential_treasury': '#6961a8', 'unresolved': '#a5b3c2'}


def esc(value):
    return html.escape(str(value))


def pct(value):
    return 'Unavailable' if value is None else f'{float(value) * 100:.1f}%'


def usd(value):
    return 'Unavailable' if value is None else f'${float(value):,.2f}'


def headline_claim(summary):
    return (f'Public receipts attribute {float(summary["attributable_share"] or 0)*100:.2f}% of '
            f'{usd(summary["total_usd"])} across {summary["count"]:,} sampled NEAR Intents swaps '
            f'to {summary["attributed_account_count"]} executing accounts; the full-sample top-three '
            f'account share remains {float(summary["top3_lower"] or 0)*100:.2f}–'
            f'{float(summary["top3_upper"] or 0)*100:.2f}%.')


def stack_chart(rows):
    width, height = 980, 50 + 52 * len(rows)
    content = [f'<svg class="coverage-chart" viewBox="0 0 {width} {height}" role="img" aria-label="USD settlement coverage by sampled date">']
    content.append('<title>Settlement coverage by sampled date</title><desc>Each bar divides valid input USD into public, confidential treasury and unresolved paths.</desc>')
    for index, row in enumerate(rows):
        y, x = 16 + index * 52, 140.0
        content.append(f'<text x="0" y="{y+16}" font-size="13">{esc(row["label"])}</text>')
        content.append(f'<rect x="140" y="{y}" width="590" height="22" fill="#f1f5fa"/>')
        for name, color in COLORS.items():
            share = float(row[f'{name}_share'] or 0)
            barwidth = share * 590
            content.append(f'<rect class="coverage-segment" style="--row-delay:{index*70}ms" x="{x:.4f}" y="{y}" width="{barwidth:.4f}" height="22" fill="{color}"><title>{esc(name)}: {pct(row[f"{name}_share"])}; {usd(row[f"{name}_usd"])}</title></rect>')
            x += barwidth
        content.append(f'<text x="750" y="{y+15}" font-size="12">{usd(row["total_usd"])} · {row["count"]} swaps</text>')
        content.append(f'<text x="140" y="{y+39}" font-size="10">Attributable {pct(row["attributable_share"])} · complete receipt USD {pct(row["rpc_complete_usd_share"])}</text>')
    return ''.join(content) + '</svg>'


def breakdown_table(rows):
    body = ''.join(f'<tr><td class="asset">{esc(r["label"])}</td><td class="num">{r["count"]}</td>'
                   f'<td class="num">{usd(r["total_usd"])}</td><td class="num">{pct(r["confidential_treasury_share"])}</td>'
                   f'<td class="num">{pct(r["attributable_share"])}</td><td class="num">{pct(r["unresolved_share"])}</td></tr>' for r in rows)
    return '<div class="table-wrap"><table><thead><tr><th>Stratum</th><th class="num">Swaps</th><th class="num">Input USD</th><th class="num">Confidential</th><th class="num">Attributed</th><th class="num">Unresolved</th></tr></thead><tbody>' + body + '</tbody></table></div>'


def source_details(csv_name, computation):
    return (f'<div class="downloads"><a href="data/{esc(csv_name)}" download>Download CSV</a>'
            '<a href="#evidence">Transaction evidence</a></div><details class="evidence-panel"><summary>Evidence: source, sample and calculation</summary>'
            '<p>Source: cached Explorer responses and linked public NEAR transaction graphs. Per-stratum sample sizes and USD denominators are in the CSV; exact window selection is linked below.</p>'
            f'<pre>{esc(computation)}</pre><a href="data/queries.json">Exact API requests for all windows</a></details>')


def observed_tiles(summary):
    unknown = float(summary['unknown_usd']) / float(summary['total_usd']) if float(summary['total_usd']) else None
    cards = [
        ('Attributed input USD', pct(summary['attributable_share']),
         'Supported executing-account attribution. Does not verify independent operators.',
         'summary.json', 'attributable_usd / total valid input_usd'),
        ('Sampled input volume', usd(summary['total_usd']),
         'Input USD in the fixed sample. Does not show daily protocol volume or fees.',
         'swaps.csv', 'sum(valid nonnegative amountInUsd), each swap counted once'),
        ('Unattributed input USD', pct(unknown),
         'Missing account attribution remains in the denominator. Does not mean all of it is confidential.',
         'summary.json', '(total_usd - attributable_usd) / total_usd'),
        ('Executing account IDs', str(summary['attributed_account_count']),
         'Distinct supported public executing accounts. Does not establish a count of independent companies.',
         'accounts.csv', 'distinct filler_account IDs among supported attributed swaps'),
        ('Linked transaction graphs', f'{summary["tx_available"]:,} / {summary["tx_total"]:,}',
         'Complete linked response graphs available. Completeness does not imply every swap is attributable.',
         'manifest.json', 'validated FINAL, reachable receipt graphs / distinct linked NEAR hashes')]
    return '<div class="stats observed-tiles">' + ''.join(
        f'<article class="metric-tile observed-tile"><span class="tile-kind">Observed sample</span><h3>{esc(title)}</h3>'
        f'<strong>{value}</strong><p class="caption">{caption}</p>'
        f'<details class="evidence-panel"><summary>Evidence</summary><p>Source: Explorer plus public NEAR RPC. '
        f'Sample: {summary["count"]} swaps in {summary["windows"]} fixed windows.</p><pre>{esc(formula)}</pre>'
        f'<a href="data/{file}">Source data</a> · <a href="data/queries.json">Exact collection queries</a></details></article>'
        for title, value, caption, file, formula in cards) + '</div>'


def distribution_chart(rows):
    if not rows:
        return '<p>No observations in this sample.</p>'
    return ''.join(f'<div class="bar-row"><div class="bar-label"><span>{esc(r["label"])}</span>'
                   f'<span>{pct(r["share"])} · {usd(r["usd"])}</span></div><div class="track">'
                   f'<div class="fill" style="width:{100*float(r["share"] or 0):.6f}%"></div></div></div>' for r in rows[:8])


def decision_panel(summary):
    metrics = ''
    for key, label in [('top1', 'Top-1 share'), ('top3', 'Top-3 share'), ('hhi', 'HHI (0–1)')]:
        fmt = (lambda value: 'Unavailable' if value is None else f'{float(value):.4f}') if key == 'hhi' else pct
        metrics += (f'<tr><th scope="row">{label}</th><td class="num">{fmt(summary[key+"_lower"])} – {fmt(summary[key+"_upper"])}</td>'
                    f'<td class="num" id="scenario-{key}-lower"></td><td class="num" id="scenario-{key}-upper"></td>'
                    f'<td class="scenario-range"><div class="scenario-track" aria-hidden="true"><span id="scenario-{key}-band"></span></div></td></tr>')
    verdict = ('Insufficient evidence under our method' if not summary['attributed_account_count']
               else 'Partial account attribution; operator independence unverified')
    observed_range = (f'Model-free top-3 account share remains between {pct(summary["top3_lower"])} and {pct(summary["top3_upper"])}.'
                      if summary['top3_lower'] is not None else 'Concentration bounds are unavailable without positive valid sampled USD.')
    return f'''<section id="decision"><div class="section-head"><h2>Can we verify solver diversification?</h2><span class="tag">Due diligence</span></div>
<div class="decision-verdict"><span class="eyebrow">Observed verdict</span><h3>{verdict}</h3><p>The classifier attributes {summary['attributed_account_count']} executing accounts and {pct(summary['attributable_share'])} of sampled input USD. {observed_range}</p></div>
<p>Use this evidence to decide whether a diversification claim is supported before relying on it in an assessment. An attribution gap does not establish a concentrated or fragile solver market.</p>
<h3>What evidence would resolve this?</h3><div class="grid-two"><div><strong>Authenticated settlement records</strong><p>Link each sampled swap and intent hash to executed filler account deltas, amounts and timestamps. An unverified claim, receipt membership proof or quote is insufficient.</p></div><div><strong>Operator mapping and disclosure coverage</strong><p>Establish which accounts belong to independent operators. Preserve the full sampled USD denominator and all unknown volume; selective participation cannot establish market-wide diversification.</p></div></div>
<div class="disclosure-panel"><div class="section-head"><h3>What would additional disclosure change?</h3><span class="tag">Hypothetical · not observed</span></div>
<p>Enter hypothetical authenticated operator contributions as percentages of the <em>entire</em> sampled input USD denominator. Each entry assumes one independent operator and disjoint volume. The remainder stays unknown. The observed column measures account IDs; the hypothetical column assumes independent operators. This separate scenario does not edit observed data, establish operator mappings or demonstrate that anyone disclosed records.</p>
<label for="disclosure-shares">Hypothetical operator shares (%)</label><textarea id="disclosure-shares" rows="2" maxlength="2600" placeholder="Example: 20, 15, 10" aria-describedby="disclosure-help disclosure-error"></textarea>
<p class="caption" id="disclosure-help">Comma-separated percentages; total at most 100. Up to 200 operators and six decimal places per share. Leave empty to assume no disclosures.</p>
<div class="disclosure-presets"><button type="button" data-disclosure-preset="">Clear scenario</button><button type="button" data-disclosure-preset="{', '.join(['4.5'] * 20)}">Example: 90% across 20 equal operators</button><button type="button" data-disclosure-preset="70, 10, 10">Example: 90%, one large operator</button></div>
<p id="disclosure-error" role="alert" hidden></p><p id="disclosure-status" role="status" aria-live="polite">Enable JavaScript to explore hypothetical disclosures.</p>
<div id="disclosure-results" hidden><div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">Observed account range</th><th class="num">Scenario lower</th><th class="num">Scenario upper</th><th>Scenario range · 0 to 1</th></tr></thead><tbody>{metrics}</tbody></table></div></div>
<p class="caption">Model-free bounds allow unknown USD to be split arbitrarily among arbitrarily many operators; the lower HHI can be an infimum. The upper assigns all unknown volume to the largest disclosed operator, or one new operator if none is disclosed. Operator independence, authenticated execution and non-overlapping volume are assumptions here. Narrower uncertainty does not itself establish diversification. Figures are rounded; small nonzero widths can round to zero.</p>
<details><summary>Scenario calculation</summary><p>Let disclosed full-denominator shares be a₁ ≥ a₂ ≥ … and remaining share U = 1 − Σa. Top-N range: [Σ top-N a, min(1, Σ top-N a + U)]. HHI range: [Σa², (a₁ + U)² + Σ other a²]. At full disclosure the bounds meet; the resulting concentration can still be high.</p></details></div></section>'''


def investment_panel(summary):
    def width(metric):
        lower, upper = summary[metric + '_lower'], summary[metric + '_upper']
        return None if lower is None or upper is None else float(upper) - float(lower)
    hhi_width = width('hhi')
    hhi_text = 'Unavailable' if hhi_width is None else f'{hhi_width:.4f}'
    return f'''<section id="investment"><div class="section-head"><h2>Investment stance: no diversification premium from volume alone</h2><span class="tag">Conditional research position</span></div>
<p>Do not use gross Intents swap volume as independently verified evidence of diversified, durable solver supply. This study supports withholding that assumption in a volume-driven bull case until settlement coverage and operator mappings make it testable. It does not establish a short position or a fair value for the NEAR token.</p>
<div class="table-wrap"><table><thead><tr><th>Research evidence gate</th><th class="num">Observed baseline</th><th>Reassessment condition</th></tr></thead><tbody>
<tr><td>Attributed input USD coverage</td><td class="num">{pct(summary['attributable_share'])}</td><td>At least 90%</td></tr>
<tr><td>Top-3 account-bound width</td><td class="num">{pct(width('top3'))}</td><td>At most 10 percentage points</td></tr>
<tr><td>HHI account-bound width</td><td class="num">{hhi_text}</td><td>At most 0.05</td></tr>
<tr><td>Independent operator mapping</td><td>Unverified</td><td>Authenticated account-to-operator evidence</td></tr></tbody></table></div>
<p class="caption">These project research gates were stated in the thesis before the corrected wider receipt analysis; they are not industry standards. Passing uncertainty gates would justify reassessment, not prove low concentration. Fees, buybacks, NEAR token value capture and liquidity replacement after maker exits have not been established here.</p>
<details><summary>What would weaken this stance?</summary><p>Authenticated records covering most sampled USD, independently mapped operators, and narrow concentration bounds showing diversified activity would weaken the auditability concern. Demonstrated continuity through independently documented maker exits would weaken a fragility hypothesis. Neither outcome is assumed. Growth, privacy and competition can coexist; privacy alone is not adverse evidence.</p></details></section>'''


def sensitivity_panel(checks):
    def table(cases):
        body = ''.join(f'<tr><td>{esc(r["label"])}</td><td class="num">{r["count"]}</td>'
                       f'<td class="num">{pct(r["attributable_share"])}</td>'
                       f'<td class="num">{pct(r["subset_top3"])}</td>'
                       f'<td class="num">{pct(r["top3_lower"])}–{pct(r["top3_upper"])}</td></tr>' for r in cases)
        return ('<div class="table-wrap"><table><thead><tr><th>Remaining sample</th><th class="num">Swaps</th>'
                '<th class="num">USD attributed</th><th class="num">Top 3 / attributed USD</th>'
                '<th class="num">Top 3 / all remaining USD</th></tr></thead><tbody>' + body + '</tbody></table></div>')
    date_cases = [r for r in checks['scenarios'] if r['scenario'].startswith('exclude_date_')]
    values = [float(r['subset_top3']) for r in date_cases if r['subset_top3'] is not None]
    leader = checks['accounts'][0] if checks['accounts'] else None
    recurrence = (f'<p><strong>Recurring observed account:</strong> <code>{esc(leader["account"])}</code> appears in '
                  f'{leader["observed_dates"]} of {checks["sampled_dates"]} sampled dates, '
                  f'{leader["observed_windows"]} windows and {leader["swap_count"]} attributable swaps. '
                  f'Its recorded contribution is {pct(leader["share_of_all_usd"])} of all sampled USD. '
                  'These are repeated account observations, not verified operator independence or replacement capacity.</p>') if leader else ''
    date_note = (f'Excluding each date in turn leaves attributed-subset top-three concentration between '
                 f'{pct(min(values))} and {pct(max(values))}.') if values else 'No date-level concentration available.'
    return ('<section id="sensitivity"><div class="section-head"><h2>Does the finding survive large-trade exclusions?</h2>'
            '<span class="tag">Post-hoc sensitivity checks</span></div>'
            f'<p>{checks["large_swap_count"]} swaps of at least $1,000 carry {pct(checks["large_swap_usd_share"])} of sampled USD. '
            f'The largest attributable swap contributes {pct(checks["largest_attributed_swap_share"])} of attributable USD.</p>'
            + recurrence + table(checks['scenarios'][:7])
            + f'<p>{date_note} Each row recomputes its own denominator; the top three can be different accounts. '
            'Unknown remaining volume stays in the full-sample bounds.</p>'
            '<details id="date-sensitivity"><summary>Exclude one sampled date at a time</summary>' + table(date_cases) + '</details>'
            '<p class="scope-box">Observed account exposure recurs, but concentration changes with large trades. '
            'These checks are descriptive, selected after examining the sample, and do not establish protocol-wide solver concentration or predict a maker exit.</p>'
            '<div class="downloads"><a href="data/sensitivity.csv" download>All exclusion checks CSV</a>'
            '<a href="data/account-persistence.csv" download>Account recurrence CSV</a>'
            '<a href="INVESTMENT_BRIEF.md">Short investment brief</a></div></section>')


def build_dashboard(report, derived=None, docs=None, *, inventory=None, economic=None):
    derived, docs = Path(derived or ROOT / 'data/derived'), Path(docs or ROOT / 'docs')
    destination = docs / 'data'
    destination.mkdir(parents=True, exist_ok=True)
    # Copy only the public evidence products, never raw responses, .env or log files.
    for name in ('swaps.csv', 'accounts.csv', 'evidence.json', 'summary.json', 'manifest.json',
                 'coverage-date.csv', 'coverage-slot.csv', 'coverage-window.csv', 'coverage-pair.csv',
                 'coverage-size.csv', 'coverage-date_pair_size.csv', 'referrals.csv', 'fee-recipients.csv',
                 'sensitivity.json', 'sensitivity.csv', 'account-persistence.csv'):
        shutil.copyfile(derived / name, destination / name)
    for name in ('dashboard.css', 'verify.js', 'disclosure.js', 'durability.js'):
        shutil.copyfile(ASSETS / name, docs / name)
    (docs / 'fonts').mkdir(exist_ok=True)
    for name in ('BebasNeue-Regular.ttf', 'OFL.txt'):
        shutil.copyfile(ASSETS / 'fonts' / name, docs / 'fonts' / name)
    summary, breakdowns = report['summary'], report['breakdowns']
    manifest = json.loads((derived / 'manifest.json').read_text())
    (destination / 'headline.txt').write_text(headline_claim(summary) + '\n', encoding='utf-8')
    checks = json.loads((derived / 'sensitivity.json').read_text())
    (docs / 'INVESTMENT_BRIEF.md').write_text(investment_brief(checks), encoding='utf-8')
    scenario = durability_inputs(report, economic=economic)
    write_json(destination / 'durability-inputs.json', scenario)
    write_json(destination / 'economic-baseline.json', scenario['economic'])
    stress = {'status': 'not_established', 'verified_stress_event': None,
              'verified_departures': None, 'sample_count': summary['count'],
              'sampled_dates': sorted({w['start'][:10] for w in manifest['windows']}),
              'windows': summary['windows'], 'window_minutes': manifest.get('sampling', {}).get('window_minutes', 2),
              'source': 'sampling.json and cached Explorer windows; linked public NEAR transaction graphs',
              'reason': 'Short, nonconsecutive windows do not establish a volatile week, continuous before/after volume, or independently verified account exits.',
              'needed': 'A dated, independently documented event and continuous comparable volume, fee and attribution observations before, during and after it.'}
    write_json(destination / 'stress-evaluation.json', stress)
    queries = []
    for window in manifest['windows']:
        start = dt.datetime.fromisoformat(window['start'].replace('Z', '+00:00')) - dt.timedelta(milliseconds=1)
        params = {'numberOfTransactions': manifest.get('sampling', {}).get('page_size', 1000),
                  'statuses': manifest.get('sampling', {}).get('statuses', 'SUCCESS'),
                  'startTimestamp': start.isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
                  'endTimestamp': window['end']}
        queries.append({'window': window['start'], 'url': 'https://explorer.near-intents.org/api/v0/transactions?' + urlencode(params),
                        'pagination': 'Continue with lastDepositAddress + lastDepositMemo until exhausted; locally filter to [start,end).',
                        'cursor': 'Page cursors were not preserved by the original collector; complete window response is cached.'})
    write_json(destination / 'queries.json', queries)
    with (derived / 'swaps.csv').open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle))
    if not summary['receipt_run_complete']:
        headline = 'Historical receipt coverage is incomplete.'
        notice = (f'<div class="notice"><p><strong>Provisional snapshot.</strong> {summary["tx_available"]:,} of '
                  f'{summary["tx_total"]:,} linked transaction results are cached. Missing receipts remain unresolved. '
                  'Coverage can change as collection completes; do not interpret this snapshot as a confidentiality trend.</p></div>')
        if summary.get('provider_refused'):
            notice += '<div class="notice"><strong>Collection stopped:</strong> the public archival endpoint explicitly refused the deprecated service. A working archival RPC endpoint is needed to resume.</div>'
    elif not float(summary['attributable_usd']):
        headline, notice = 'Executing accounts remain unattributed.', ''
    else:
        headline, notice = f'Attribution covers {pct(summary["attributable_share"])} of sampled volume.', ''
    legend = '<div class="legend"><span class="public">Public settlement</span><span class="private">Confidential treasury</span><span>Unresolved</span></div>'
    ribbon = ''.join(f'<span style="background:{color};width:{100*float(summary[name+"_share"] or 0):.6f}%" title="{esc(name)}: {pct(summary[name+"_share"])}"></span>' for name, color in COLORS.items())
    bounds_rows = ''
    for key, label in [('top1', 'Top-1 share'), ('top3', 'Top-3 share'), ('top10', 'Top-10 share'), ('hhi', 'HHI (0–1)')]:
        fmt = (lambda value: 'Unavailable' if value is None else f'{float(value):.4f}') if key == 'hhi' else pct
        bounds_rows += f'<tr><td>{label}</td><td class="num">{fmt(summary["subset_"+key])}</td><td class="num">{fmt(summary[key+"_lower"])}</td><td class="num">{fmt(summary[key+"_upper"])}</td></tr>'
    conditional_bounds_rows = ''
    for key, label in [('top1', 'Top-1 share'), ('top3', 'Top-3 share'), ('top10', 'Top-10 share'), ('hhi', 'HHI (0–1)')]:
        fmt = (lambda value: 'Unavailable' if value is None else f'{float(value):.4f}') if key == 'hhi' else pct
        conditional_bounds_rows += (f'<tr><td>{label}</td>'
                                    f'<td class="num">{fmt(summary["one_swap_one_filler_"+key+"_lower"])}</td>'
                                    f'<td class="num">{fmt(summary["one_swap_one_filler_"+key+"_upper"])}</td></tr>')
    account_rows = ''.join(f'<tr><td class="asset"><code>{esc(row["account"])}</code></td>'
                           f'<td class="num">{usd(row["usd"])}</td>'
                           f'<td class="num">{pct(float(row["usd"]) / float(summary["attributable_usd"]))}</td>'
                           f'<td class="num">{pct(float(row["usd"]) / float(summary["total_usd"]))}</td></tr>'
                           for row in sorted(report['accounts'], key=lambda row: -float(row['usd']))[:8])
    account_table = ('<h3>Largest observed executing accounts</h3><p>Shares within the attributable subset do not describe the unknown volume. Account IDs are not verified independent operators; aliases are not merged.</p>'
                     '<div class="table-wrap"><table><thead><tr><th>Executing account</th><th class="num">Attributed input USD</th><th class="num">Share of attributed USD</th><th class="num">Share of all sampled USD</th></tr></thead><tbody>'
                     + account_rows + '</tbody></table></div><p class="caption">Largest eight accounts shown; all account totals are in the downloadable CSV.</p>') if account_rows else ''
    evidence_rows = []
    for row in rows:
        txs = json.loads(row['near_tx_hashes'])
        links = ''.join(f'<a href="https://nearblocks.io/txns/{quote(tx, safe="")}" target="_blank" rel="noopener noreferrer">{esc(tx[:12])}…</a>' for tx in txs)
        evidence_rows.append(f'<tr id="swap-{row["swap_id"]}"><td>{esc(row["window"][:16])}<br><code>{row["swap_id"]}</code></td>'
                             f'<td class="asset">{esc(row["origin_asset"])}<br>→ {esc(row["destination_asset"])}</td>'
                             f'<td class="num">{usd(row["input_usd"] or None)}</td><td>{esc(row["settlement_class"])}<br>'
                             f'<span class="caption">{esc(row["reason"])}</span></td><td class="tx-links">{links}</td></tr>')
    payload = json.dumps({'csv': (derived / 'swaps.csv').read_text(encoding='utf-8'), 'summary': summary}, ensure_ascii=True, sort_keys=True).replace('<', '\\u003c')
    window_dates = sorted({window['start'][:10] for window in manifest['windows']})
    parse_time = lambda value: dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    minutes = sum((parse_time(w['end']) - parse_time(w['start'])).total_seconds() for w in manifest['windows']) / 60
    scope = f'{summary["windows"]} fixed UTC windows · {minutes:g} minutes · {summary["count"]:,} successful swaps · {window_dates[0]} to {window_dates[-1]}'
    coverage_source = source_details('coverage-date.csv', 'Class share = sum(valid amountInUsd in class) / sum(valid amountInUsd).\nAttributed share = sum(USD with supported filler_account) / total valid USD.\nDate means three predeclared two-minute UTC windows, not a full day.')
    bounds_source = source_details('accounts.csv', 'Let attributed account volumes be a1 >= a2 >= ..., unknown USD U, total T.\nModel-free Top-N: [sum(top N a)/T, min(1,(sum(top N a)+U)/T)].\nModel-free HHI: [sum(a²)/T², ((a1+U)²+sum(other a²))/T²].\nConditional one-swap/one-filler lower bound: treat each unattributed swap USD as one indivisible account volume and assign every one to a distinct account; preserve already attributed account totals. Upper bound assigns unknown volume to the largest known account or one new account.\nThe conditional model is not evidence that a swap has one filler. T=0 makes ratios unavailable.')
    size_source = source_details('coverage-size.csv', 'Bin on amountInUsd: [0,100), [100,1000), [1000,infinity).\nNo input/output USD API filter was applied to the main sample.')
    fee_source = source_details('fee-recipients.csv', 'For each distinct appFees.recipient on a swap, count that swap amountInUsd once.\nShares overlap and may sum above 100%. This is routed swap volume, not fee revenue.')
    warehouse = inventory if inventory is not None else load_inventory()
    warehouse_section = render_inventory(warehouse, docs)
    warehouse_status = ('Executed event inventory across 24 windows; no swap-level reconciliation or solver attribution.'
                        if warehouse else 'Incomplete: no imported warehouse event inventory.')
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lithium — What can public receipts reveal?</title><meta name="description" content="Reproducible research into NEAR Intents attribution coverage and account concentration uncertainty.">
<link rel="stylesheet" href="dashboard.css"><script src="verify.js" defer></script><script src="disclosure.js" defer></script><script src="durability.js" defer></script></head><body>
<header id="research"><nav aria-label="Main navigation"><a class="brand" href="#">Lithium</a><div class="nav-links"><a href="#durability">Durability</a><a href="#coverage">Coverage</a><a href="#bounds">Concentration</a><a href="#stress">Stress evidence</a><a href="#bigquery">BigQuery</a><a href="#evidence">Evidence</a></div></nav>
<div class="hero"><div class="eyebrow">NEAR Intents / Public evidence study</div><h1>{headline}</h1><p class="lead">{headline_claim(summary)}</p><p class="scope">{scope}</p></div>{notice}
<aside id="analyst-checklist" class="action-checklist" aria-labelledby="analyst-checklist-title"><h2 id="analyst-checklist-title">What to demand before trusting diversification</h2><ul><li><strong>Authenticated settlement links:</strong> swaps and intents tied to executed amounts, including confidential paths.</li><li><strong>Independent operator mappings:</strong> account ownership and aliases.</li><li><strong>Coverage and economics:</strong> complete volume denominators and reconciled fees versus captured revenue.</li><li><strong>Continuity evidence:</strong> before/during/after a documented departure, including replacement activity.</li></ul><p>Until then, test assumptions; do not infer diversified solver supply from gross volume.</p></aside>
<div class="ribbon" role="img" aria-label="Overall settlement-class shares of valid input USD">{ribbon}</div>{legend}
<p class="caption"><strong>Shows:</strong> settlement-route shares of sampled input USD. <strong>Does not show:</strong> independent solver identities or measured revenue.</p>
{observed_tiles(summary)}</header>
<main>{durability_panel(scenario)}<section id="stress"><div class="section-head"><h2>Real stress event: not established</h2><span class="tag">Evidence gap</span></div><p>The current short, nonconsecutive windows do not establish a volatile week or independently documented solver departure. There is no measured before/during/after fee or revenue series. An account missing from a two-minute window is not a verified exit.</p><p>Trade/date exclusions below are sensitivity checks, not historical stress events. Testing replacement capacity requires a dated event and continuous comparable observations before, during and after it.</p><details class="evidence-panel"><summary>Stress assessment evidence</summary><p>Scope: {summary['count']} swaps, {summary['windows']} fixed windows; source: Explorer and linked public NEAR receipts. No external event or price series has been joined to this sample.</p><a href="data/stress-evaluation.json">Machine-readable assessment</a> · <a href="data/queries.json">Collection queries and dates</a></details></section>{decision_panel(summary)}{investment_panel(summary)}<section id="coverage"><div class="section-head"><h2>Where public visibility ends</h2><span class="tag">USD-weighted coverage</span></div><p>Bars show the settlement evidence for each sampled date; executing-account attribution is reported separately beneath each bar.</p>{legend}{stack_chart(breakdowns['date'])}
<p class="caption"><strong>Shows:</strong> USD settlement classes in three two-minute windows per sampled date. <strong>Does not show:</strong> whole-day activity, private solver identities or a protocol-wide trend.</p>
<p class="caption">Denominator: valid, nonnegative amountInUsd in each date's three windows. {summary['invalid_usd_count']} records have unavailable or invalid USD and are excluded from USD metrics. Sampled dates are exploratory comparisons, not daily or protocol-wide estimates.</p>
{coverage_source}
<details><summary>Exact figures by date</summary>{breakdown_table(breakdowns['date'])}</details></section>
<section id="bounds"><div class="section-head"><h2>Full-sample account concentration remains uncertain</h2><span class="tag">Identifiability bounds</span></div><p>{usd(summary['attributable_usd'])} is attributable to {summary['attributed_account_count']} executing accounts. The public evidence cannot rule out either many fillers or one dominant filler. Confidential-treasury settlement is {pct(summary['confidential_treasury_share'])} of sampled USD; that identifies a route, not a solver.</p>
<div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">Attributed subset</th><th class="num">Full sample lower bound</th><th class="num">Full sample upper bound</th></tr></thead><tbody>{bounds_rows}</tbody></table></div>
<p class="caption">These model-free outer bounds assume unknown volume can be split arbitrarily among accounts. They are uncertainty ranges, not confidence intervals. Account IDs are not independently verified operators.</p>
{account_table}
<h3>Conditional scenario: one filler per swap</h3><p>Assume each of {summary['one_swap_one_filler_assumed_fill_count']} sampled swaps is exactly one indivisible fill. The lower bound assigns each unattributed swap to a different filler; the upper assigns them together. This is a sensitivity case, not an observed fill count or a verified settlement structure.</p>
<div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">Most dispersed</th><th class="num">Most concentrated</th></tr></thead><tbody>{conditional_bounds_rows}</tbody></table></div>
{bounds_source}<div class="downloads"><a href="data/summary.json">All figures and bounds</a><a href="data/swaps.csv" download>Full denominator CSV</a></div></section>
{sensitivity_panel(checks)}
<section id="strata"><h2>Pairs and sizes change the picture</h2><p>These strata preserve composition differences that an aggregate time comparison can hide.</p><h3>Input USD size</h3>{breakdown_table(breakdowns['size'])}{size_source}
<details><summary>Asset pairs — largest 20 by sampled USD</summary>{breakdown_table(sorted(breakdowns['pair'], key=lambda r: -float(r['total_usd']))[:20])}</details>{source_details('coverage-pair.csv', 'Group by directed (originAsset,destinationAsset); compute class and attributed USD shares within each pair.')}<div class="downloads"><a href="data/coverage-slot.csv" download>UTC slots</a><a href="data/coverage-window.csv" download>All windows</a><a href="data/coverage-date_pair_size.csv" download>Date × pair × size cells</a></div></section>
<section id="distribution"><div class="section-head"><h2>A different dependency: distribution</h2><span class="tag">Secondary analysis</span></div><p>Referral and fee-routing fields describe distribution relationships. They do not identify market makers.</p><div class="grid-two"><div><h3>Referral volume</h3>{distribution_chart(report['distributions']['referrals'])}
<p class="caption"><strong>Shows:</strong> sampled input volume grouped by referral. <strong>Does not show:</strong> fee revenue, solver market share or independent operators.</p>
{source_details('referrals.csv', 'Sum each swap amountInUsd once by its referral. Missing referral remains a separate unknown category. Shares use all valid sampled USD.')}</div><div><h3>Fee recipient incidence</h3>{distribution_chart(report['distributions']['fee-recipients'])}
<p class="caption"><strong>Shows:</strong> sampled volume mentioning each fee recipient. <strong>Does not show:</strong> fees earned. A swap may mention multiple recipients, so shares overlap.</p>
{fee_source}</div></div><p class="caption">Largest eight entries shown; CSVs contain every observed label. Fee-recipient shares overlap.</p></section>
{warehouse_section}
<section id="verification"><h2>Check the arithmetic here</h2><p>Your browser recomputes USD coverage, attributed-subset concentration and the outer bounds from the shipped swap CSV.</p><div class="check" id="browser-check" role="status" aria-live="polite" data-status="pending">Checking CSV arithmetic…</div><noscript><p>Enable JavaScript for the browser recheck. CSVs and all chart figures remain available.</p></noscript><div class="downloads"><a href="data/swaps.csv" download>Source CSV</a><a href="data/manifest.json">Provenance manifest</a><a href="data/evidence.json">Supporting receipt events</a></div><p class="caption">When opened directly as a local file, the check uses the identical CSV copy embedded at build time. Over HTTP it loads data/swaps.csv. This checks published arithmetic, not the truth of an RPC provider or private FAR settlement. The separate warehouse event inventory is not part of this USD arithmetic check.</p></section>
<section id="evidence"><h2>Follow the receipts</h2><p>Every sampled swap keeps its classification reason and all linked transaction hashes. Supporting events and receipt IDs are in the downloadable evidence extract.</p><label for="evidence-search">Filter by date, asset, transaction or classification</label><input id="evidence-search" type="search" placeholder="Search this sample…"><div class="table-wrap"><table id="evidence-table"><thead><tr><th>UTC window / swap ID</th><th>Asset path</th><th class="num">Input USD</th><th>Classification / reason</th><th>Linked transactions</th></tr></thead><tbody>{''.join(evidence_rows)}</tbody></table></div><div class="downloads"><a href="data/evidence.json">Structured events</a><a href="data/swaps.csv" download>All sampled swaps</a></div></section>
<section id="method"><h2>What this evidence can establish</h2><ol class="method-list"><li><strong>Sample.</strong> {summary['windows']} fixed UTC windows on {len(window_dates)} dates: {minutes:g} minutes total. Each window is fully paginated. This designed convenience sample is not representative of continuous activity across these dates.</li><li><strong>Link.</strong> Inspect every linked NEAR transaction. A confidential classification requires origin-asset shielding and destination-asset release for an account linked to the swap's intent hashes. Shared treasury co-occurrence is insufficient.</li><li><strong>Attribute.</strong> A public token_diff must link to the swap. In a single execution receipt with exactly two token_diff accounts, all customer entries must match the swap intent hashes. Aggregate every account delta and reported protocol fee; require exact per-token closure and opposing input/output directions. Multi-account batches, unmatched fees or extra customer executions remain unattributed. This conservative rule can miss identifiable executions.</li><li><strong>Separate access failures.</strong> Missing hashes, unavailable archival receipts, failed execution and unsupported event shapes remain unresolved. No relayer, bridge signer or shared treasury is counted as a solver.</li><li><strong>Resolve the unknown.</strong> An authorized FAR settlement export must link swap IDs and intent hashes to executed signed account deltas, amounts and timestamps. Operator mapping is additionally needed for company-level concentration.</li></ol>
<p class="scope-box"><strong>BigQuery:</strong> {warehouse_status} USD coverage and concentration bounds use Explorer and NEAR RPC. Warehouse event counts have a separate denominator and do not identify private FAR executions.</p><p class="scope-box">Limited public auditability constrains verification of solver dependence. It does not establish fragile liquidity, concentrated operators or a bearish token valuation.</p><div class="downloads"><a href="ATTRIBUTION_AUDIT.md">Classifier correction and real-receipt audit</a><a href="SPIKE_RESULT.md">Initial five-swap spike</a><a href="data/queries.json">Explorer queries</a><a href="data/manifest.json">Cache hashes and sampling scope</a></div><p class="caption">Sources: <a href="https://docs.near-intents.org/integration/market-makers/confidential-intents">Confidential Intents architecture</a>; <a href="https://explorer.near-intents.org/api/v0/openapi.yaml">Explorer schema</a>; <a href="https://docs.near.org/api/rpc/providers">archival RPC documentation</a>.</p></section></main>
<footer>Lithium · NEAR Intents investment research · Scenarios, not predictions. Not financial advice.</footer>
<script type="application/json" id="verification-input">{payload}</script></body></html>'''
    (docs / 'index.html').write_text(page, encoding='utf-8')
    conditional_hhi = summary['one_swap_one_filler_hhi_lower']
    conditional_hhi_text = 'Unavailable' if conditional_hhi is None else f'{float(conditional_hhi):.4f}'
    result_lines = ['# Latest cached analysis', '',
                    '**Status: ' + ('complete receipt collection' if summary['receipt_run_complete'] else 'provisional; receipt coverage incomplete') + '.**', '',
                    f'- Successful sampled swaps: {summary["count"]}.',
                    f'- Valid input USD: {summary["total_usd"]}.',
                    f'- Linked transaction responses available: {summary["tx_available"]}/{summary["tx_total"]}.',
                    f'- Swaps with complete receipt graphs for every linked transaction: {summary["rpc_complete_count"]}.',
                    f'- Supported executing accounts: {summary["attributed_account_count"]}.',
                    f'- Attributed input USD: {summary["attributable_usd"]}.',
                    f'- Confidential-treasury input USD: {summary["confidential_treasury_usd"]} ({pct(summary["confidential_treasury_share"])}).',
                    f'- Conditional one-swap/one-filler lower bounds: top-1 {pct(summary["one_swap_one_filler_top1_lower"])}, top-3 {pct(summary["one_swap_one_filler_top3_lower"])}, HHI {conditional_hhi_text}.',
                    '- BigQuery: ' + warehouse_status, '',
                    '## Coverage by sampled date', '',
                    '| Date | Swaps | Valid input USD | Confidential treasury USD | Public USD | Unresolved USD |',
                    '| --- | ---: | ---: | ---: | ---: | ---: |']
    for row in breakdowns['date']:
        result_lines.append(f'| {row["label"]} | {row["count"]} | {row["total_usd"]} | {row["confidential_treasury_usd"]} | {row["public_usd"]} | {row["unresolved_usd"]} |')
    result_lines.extend(['', f'These figures describe {summary["windows"]} fixed windows ({minutes:g} minutes), not full days or the protocol.',
                         'All linked transaction response graphs are complete for this sample; unsupported or ambiguous evidence remains unclassified. This convenience sample cannot establish a protocol-wide confidentiality trend.',
                         'Unattributed volume does not prove concentrated or fragile liquidity.', '',
                         'See [summary.json](data/summary.json), [swaps.csv](data/swaps.csv), and [manifest.json](data/manifest.json).', ''])
    (docs / 'RESULTS.md').write_text('\n'.join(result_lines), encoding='utf-8')
    return docs / 'index.html'
