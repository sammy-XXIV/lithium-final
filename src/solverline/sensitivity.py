"""Descriptive trade/date exclusions; no resampling or operator inference."""
from collections import Counter, defaultdict
from decimal import Decimal

from .analyze import aggregate, money, ratio, text, swap_id


def sensitivity(rows, *, identity=swap_id):
    rows = sorted(rows, key=lambda r: (r['createdAt'], identity(r)))
    valid = [r for r in rows if money(r.get('amountInUsd')) is not None]
    known = [r for r in valid if r.get('filler_account') and r.get('attribution_status') == 'attributed'
             and r['settlement_class'] == 'public']
    ranking = lambda rs: sorted(rs, key=lambda r: (-money(r['amountInUsd']), r['createdAt'], identity(r)))
    ranked, known_ranked = ranking(valid), ranking(known)
    total = sum((money(r['amountInUsd']) for r in valid), Decimal(0))
    attributed = sum((money(r['amountInUsd']) for r in known), Decimal(0))
    scenarios = []

    def case(name, label, removed):
        ids = {identity(r) for r in removed}
        remaining = [r for r in rows if identity(r) not in ids]
        scenarios.append({'scenario': name, 'label': label, 'removed_count': len(removed),
                          'removed_usd': text(sum((money(r['amountInUsd']) or Decimal(0) for r in removed), Decimal(0))),
                          'removed_swap_ids': sorted(ids), **aggregate(remaining)})

    case('baseline', 'All sampled swaps', [])
    for scope, pool in (('all', ranked), ('attributed', known_ranked)):
        for n in (1, 5, 10):
            case(f'exclude_largest_{n}_{scope}', f'Exclude largest {n} {scope} swap(s)', pool[:n])
    dates = sorted({r['sample_window'][:10] for r in rows})
    for date in dates:
        case('exclude_date_' + date, 'Exclude sampled date ' + date,
             [r for r in rows if r['sample_window'][:10] == date])
    accounts = defaultdict(list)
    for row in known:
        accounts[row['filler_account']].append(row)
    persistence = []
    for account, trades in accounts.items():
        amounts = [money(r['amountInUsd']) for r in trades]
        volume = sum(amounts, Decimal(0))
        persistence.append({'account': account, 'swap_count': len(trades),
                            'observed_dates': len({r['sample_window'][:10] for r in trades}),
                            'observed_windows': len({r['sample_window'] for r in trades}),
                            'input_usd': text(volume), 'share_of_all_usd': ratio(volume, total),
                            'largest_swap_share_of_account_usd': ratio(max(amounts), volume)})
    persistence.sort(key=lambda r: (-Decimal(r['input_usd']), r['account']))
    pairs = Counter((r['originAsset'], r['destinationAsset']) for r in rows)
    return {'method': 'Post-hoc descriptive sensitivity. Remove complete swaps, recompute USD denominators and keep all remaining unknown volume. No confidence interval, causal exit model or protocol-wide estimate.',
            'scenarios': scenarios, 'accounts': persistence, 'sampled_dates': len(dates),
            'largest_attributed_swap_share': ratio(money(known_ranked[0]['amountInUsd']), attributed) if known else None,
            'large_swap_count': sum(money(r['amountInUsd']) >= 1000 for r in valid),
            'large_swap_usd_share': ratio(sum((money(r['amountInUsd']) for r in valid if money(r['amountInUsd']) >= 1000), Decimal(0)), total),
            'pair_count': len(pairs), 'singleton_pair_count': sum(n == 1 for n in pairs.values())}


def investment_brief(checks):
    """Keep the short brief's figures tied to the same computed exclusions."""
    pct = lambda value: 'unavailable' if value is None else f'{Decimal(value) * 100:.2f}%'
    cases = {r['scenario']: r for r in checks['scenarios']}
    baseline = cases['baseline']
    leader = checks['accounts'][0] if checks['accounts'] else None
    dates = [Decimal(r['subset_top3']) for name, r in cases.items()
             if name.startswith('exclude_date_') and r['subset_top3'] is not None]
    lines = ['# Investment brief: recurring account exposure, uncertain market concentration', '',
             '**Decision:** do not credit independent solver diversification to gross Intents volume alone. '
             'Request authenticated settlement coverage and operator mapping before relying on it in a durability case.', '',
             '## What the evidence establishes', '',
             f'- {baseline["count"]} sampled swaps; ${Decimal(baseline["total_usd"]):,.2f} input volume. '
             f'{pct(baseline["attributable_share"])} is attributable to executing accounts.',
             f'- The largest three account for {pct(baseline["subset_top3"])} of attributable USD, '
             f'but the full-sample account top-three interval is {pct(baseline["top3_lower"])}–{pct(baseline["top3_upper"])}.']
    if leader:
        lines.append(f'- `{leader["account"]}` appears in {leader["observed_dates"]} of {checks["sampled_dates"]} sampled dates '
                     f'and {leader["swap_count"]} attributable swaps. Its recorded exposure is {pct(leader["share_of_all_usd"])} '
                     'of sampled USD. This is repeated account involvement, not a company-level identity claim.')
    lines += ['', '## What survives the sensitivity checks', '',
              '| Exclusion | Remaining swaps | Attributable USD coverage | Top three / attributable USD | Top three / all remaining USD |',
              '| --- | ---: | ---: | ---: | ---: |']
    for name in ('baseline', 'exclude_largest_1_all', 'exclude_largest_5_all', 'exclude_largest_10_all',
                 'exclude_largest_1_attributed', 'exclude_largest_5_attributed', 'exclude_largest_10_attributed'):
        r = cases[name]
        lines.append(f'| {r["label"]} | {r["count"]} | {pct(r["attributable_share"])} | {pct(r["subset_top3"])} | '
                     f'{pct(r["top3_lower"])}–{pct(r["top3_upper"])} |')
    if dates:
        lines += ['', f'Leaving out each sampled date in turn gives attributed-subset top-three shares of '
                  f'{pct(min(dates))}–{pct(max(dates))}. Top-three membership can change between checks.']
    lines += ['', f'The largest attributable trade supplies {pct(checks["largest_attributed_swap_share"])} of attributable USD. '
              f'{checks["large_swap_count"]} swaps of at least $1,000 carry {pct(checks["large_swap_usd_share"])} of all sampled USD. '
              'Large trades materially affect the headline. Every exclusion removes complete swaps and recomputes both known and unknown denominators.', '',
              '## Evidence against a stronger claim', '',
              'The study covers 48 minutes across eight dates, not continuous activity or a probability sample. '
              'The classifier declines ambiguous executions, so missing attribution is partly a method limit. '
              'Account aliases may share an operator; counterparties may replace an exiting maker. Neither independent operator concentration '
              'nor lost-volume effects are measured. These exclusions were selected after inspecting the sample; they are not confidence intervals.', '',
              f'{checks["singleton_pair_count"]} of {checks["pair_count"]} directed asset pairs appear only once. '
              'Sparse pair cells cannot support a reliable pair-level dependency ranking.', '',
              '## What would change the decision', '',
              'Authenticated, coverage-audited settlements and independently verified operator mappings could resolve the unknown share. '
              'The thesis uses project research gates of at least 90% attributed USD, top-three interval width at most 10 percentage points '
              'and HHI width at most 0.05. These are not industry standards or automatic buy signals; fuller disclosure could reveal high concentration.', '',
              'The actionable conclusion is to keep solver diversification unverified while documenting the observed account exposure. '
              'It is not a bearish NEAR price call, a forecast of liquidity loss or a measurement of token-holder value capture.', '',
              '[All exclusions](data/sensitivity.csv) · [Account recurrence](data/account-persistence.csv) · '
              '[Full methodology and thesis](https://github.com/sammy-XXIV/lithium-final/blob/main/THESIS.md)', '']
    return '\n'.join(lines)
