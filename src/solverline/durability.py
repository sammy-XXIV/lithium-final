"""Static, explicitly conditional account-exit and fee/revenue scenarios."""
import html
import json
import math

from .pull_explorer import ROOT


def make_inputs(report):
    summary = report['summary']
    dates = sorted(report['breakdowns']['date'], key=lambda r: r['label'])
    coverage = [float(r['attributable_share']) for r in dates if r['attributable_share'] is not None]
    changes = [float(b['total_usd']) / float(a['total_usd']) - 1 for a, b in zip(dates, dates[1:]) if float(a['total_usd'])>0]
    economic = json.loads((ROOT / 'data/inputs/economic-baseline.json').read_text())
    return {'totalUsd': summary['total_usd'], 'accounts': report['accounts'],
            'observedCoverage': float(summary['attributable_share'] or 0),
            'dateCoverageRange': [min(coverage), max(coverage)] if coverage else None,
            'sampleDateVolumeChangeRange': [min(changes), max(changes)] if changes else None,
            'volumeSliderMaximum': max(100, math.ceil(max(changes, default=1)*100/25)*25),
            'sampleCount': summary['count'], 'windows': summary['windows'],
            'transactionCount': summary['tx_total'], 'transactionsAvailable': summary['tx_available'],
            'economic': economic}


def render(data):
    escape = lambda value: html.escape(str(value))
    pct = lambda value: f'{value*100:.2f}%'
    coverage_range = 'Unavailable' if not data['dateCoverageRange'] else '–'.join(pct(v) for v in data['dateCoverageRange'])
    volume_range = 'Unavailable' if not data['sampleDateVolumeChangeRange'] else ' to '.join(pct(v) for v in data['sampleDateVolumeChangeRange'])
    economic = data['economic']
    fee_label = f'${float(economic["gross_fees_annualized_usd"])/1e6:.2f}M/year'
    revenue_label = f'${float(economic["captured_revenue_annualized_usd"])/1e6:.2f}M/year'
    def evidence(formula, external=False):
        source = (f'<a href="{escape(economic["source_url"])}">near-thesis Q5, pinned external input</a>; '
                  f'{escape(economic["window"])} as of {escape(economic["as_of"])}. Not independently reconciled by Lithium.'
                  if external else 'Explorer and public NEAR RPC; sampled USD and account weights, not fee receipts.')
        return (f'<details class="evidence-panel"><summary>Evidence and equation</summary><p>Source: {source}</p>'
                f'<p>Account mix: {data["sampleCount"]} swaps / {data["windows"]} fixed windows. '
                'The hypothetical coverage and departures do not change these observations.</p>'
                f'<pre>{escape(formula)}</pre><a href="data/durability-inputs.json">Model inputs</a> · '
                '<a href="data/queries.json">Exact sample queries</a></details>')
    # Embedded data keeps the exact same model usable over file:// without fetch.
    payload = json.dumps(data, ensure_ascii=True).replace('<', '\\u003c')
    return f'''<section id="durability" aria-labelledby="durability-title">
<div class="section-head"><h2 id="durability-title">How much revenue could depend on departing accounts?</h2><span class="tag">Scenarios, not predictions</span></div>
<p>Thesis to test: Intents revenue is only as durable as its solver base. This model tests a conditional exposure, not a proven causal relationship. Other makers may replace departing activity.</p>
<p class="scope-box"><strong>Model assumptions:</strong> no replacement or rerouting after exits; constant fee yield, capture fraction and price; and the sampled account-volume mix represents revenue-bearing activity. These assumptions are unverified. The model's lower loss bound is not a proven minimum loss: actual loss could be zero with replacement.</p>
<div class="scenario-controls">
<label for="durability-coverage">Assumed attributable USD share <output id="coverage-assumption"></output><input id="durability-coverage" type="range" min="0" max="100" step="0.000001" value="{data['observedCoverage']*100:.6f}"><span class="caption">Observed baseline {pct(data['observedCoverage'])}; sampled-date slice range {coverage_range}. This assumption retains the observed account mix and does not reveal new identities.</span></label>
<label for="durability-leaving">Top observed accounts leaving (solver proxy) <output id="leaving-assumption"></output><input id="durability-leaving" type="range" min="0" max="{len(data['accounts'])}" step="1" value="{1 if data['accounts'] else 0}"><span class="caption">No verified historical departure count. The 0–{len(data['accounts'])} scenario range comes from observed account IDs, not observed solver exits or independent companies.</span></label>
<label for="durability-volume">Assumed volume change before departures <output id="volume-assumption"></output><input id="durability-volume" type="range" min="-100" max="{data['volumeSliderMaximum']}" step="1" value="0"><span class="caption">Changes between sampled six-minute date slices: {volume_range}. These are nonconsecutive slices, not measured market-wide changes or stress events. Slider endpoints are model controls, not historical bounds.</span></label>
</div><button id="durability-reset" type="button">Reset assumptions</button><p id="durability-status" role="status" aria-live="polite"></p>
<p class="caption">At-risk outputs measure incremental exposure to the selected departures after the assumed volume change. They exclude changes caused by the volume assumption itself. A 100% volume decline leaves no remaining flow exposed to an additional departure.</p>
<noscript><p>Enable JavaScript to calculate scenarios. The observed evidence and model inputs remain available below.</p></noscript>
<div class="scenario-tiles">
<article class="metric-tile"><span class="tile-kind">Scenario / share</span><h3>Volume exposure</h3><strong id="risk-share">Unavailable</strong><div class="risk-band" role="img" aria-label="Conditional exposure interval on a zero to one hundred percent scale"><span id="risk-interval"></span></div><p class="caption">Shows the modeled exposure interval on a 0–100% scale. Does not predict lost volume.</p>{evidence('exposure = [c*s, c*s+(1-c)]; zero departures imply [0,0]')}</article>
<article class="metric-tile"><span class="tile-kind">Scenario / sampled USD</span><h3>Sample-scope volume at risk</h3><strong id="risk-volume">Unavailable</strong><p class="caption">USD across the scaled {data['sampleCount']}-swap sample. Not daily or annual protocol volume.</p>{evidence('sampled input USD * (1+volume change) * exposure interval')}</article>
<article class="metric-tile"><span class="tile-kind">Scenario / external USD per year</span><h3>Annualized gross fees at risk</h3><strong id="risk-fees">Unavailable</strong><p class="caption">Scenario applied to external {fee_label} gross-fee input, including affiliates. Not measured lost fees or NEAR revenue.</p>{evidence('external gross fees * (1+volume change) * exposure interval', True)}</article>
<article class="metric-tile"><span class="tile-kind">Scenario / external USD per year</span><h3>Annualized captured revenue at risk</h3><strong id="risk-revenue">Unavailable</strong><p class="caption">Scenario applied to external {revenue_label} captured-revenue input. Not a loss forecast.</p>{evidence('external captured revenue * (1+volume change) * exposure interval', True)}</article>
<article class="metric-tile"><span class="tile-kind">Scenario / external USD per year</span><h3>Durable revenue — scenario range</h3><strong id="durable-revenue">Unavailable</strong><p class="caption">Remaining annualized captured revenue under this model. Unexposed does not mean guaranteed durable, and run rates are not realized annual revenue.</p>{evidence('external captured revenue * (1+volume change) * [1-upper exposure, 1-lower exposure]', True)}</article>
</div>
<details class="evidence-panel"><summary>Model evidence, source and equations</summary>
<p>Observed scope: {data['sampleCount']} swaps in {data['windows']} fixed two-minute windows; {data['transactionsAvailable']} of {data['transactionCount']} linked transaction graphs available. Account identity is a proxy, not operator verification. Source: Explorer plus NEAR RPC.</p>
<p>External economics: <a href="{escape(economic['source_url'])}">Andrea Soldano's near-thesis, Q5</a>, snapshot {escape(economic['as_of'])}, trailing 90 days annualized. These rounded published inputs are not independently reconciled by Lithium. They use a different denominator and period from the sampled trades; transporting the account mix to them is an assumption.</p>
<p>Departing account IDs: <code id="departing-accounts">Unavailable</code>.</p>
<pre>c = assumed attributable USD share
s = departing accounts' share within attributable USD
exposure = [c*s, c*s + (1-c)] for at least one departure; [0,0] for none
g = 1 + assumed volume change
sample volume at risk = sampled USD * g * exposure
gross fees / captured revenue at risk = respective annualized input * g * exposure
remaining revenue = captured input * g * [1-exposure.upper, 1-exposure.lower]</pre>
<p>All missing attribution may belong to departing accounts or elsewhere. Moving c keeps the observed within-attributed distribution fixed. The two endpoints are conditional assignment extremes, not probabilities or confidence bounds.</p>
<div class="downloads"><a href="data/durability-inputs.json">All model inputs</a><a href="data/economic-baseline.json">External citation and provenance</a><a href="data/accounts.csv">Observed account weights</a><a href="data/coverage-date.csv">Sampled-date ranges</a><a href="data/queries.json">Exact collection queries</a></div></details>
<p class="caption"><strong>Shows:</strong> sensitivity to explicit attribution, exit and volume assumptions. <strong>Does not show:</strong> actual departures, replacement capacity, future revenue or a NEAR valuation. Not financial advice.</p>
<script type="application/json" id="durability-input">{payload}</script></section>'''
