# Investment brief: recurring account exposure, uncertain market concentration

**Decision:** do not credit independent solver diversification to gross Intents volume alone. Request authenticated settlement coverage and operator mapping before relying on it in a durability case.

## What the evidence establishes

- 555 sampled swaps; $836,107.52 input volume. 28.37% is attributable to executing accounts.
- The largest three account for 91.31% of attributable USD, but the full-sample account top-three interval is 25.91%–97.53%.
- `crux-solver.near` appears in 7 of 8 sampled dates and 21 attributable swaps. Its recorded exposure is 18.30% of sampled USD. This is repeated account involvement, not a company-level identity claim.

## What survives the sensitivity checks

| Exclusion | Remaining swaps | Attributable USD coverage | Top three / attributable USD | Top three / all remaining USD |
| --- | ---: | ---: | ---: | ---: |
| All sampled swaps | 555 | 28.37% | 91.31% | 25.91%–97.53% |
| Exclude largest 1 all swap(s) | 554 | 38.30% | 91.31% | 34.98%–96.67% |
| Exclude largest 5 all swap(s) | 550 | 34.66% | 84.98% | 29.46%–94.79% |
| Exclude largest 10 all swap(s) | 545 | 40.59% | 82.85% | 33.63%–93.04% |
| Exclude largest 1 attributed swap(s) | 554 | 18.65% | 84.98% | 15.85%–97.20% |
| Exclude largest 5 attributed swap(s) | 550 | 13.92% | 78.71% | 10.95%–97.04% |
| Exclude largest 10 attributed swap(s) | 545 | 10.85% | 71.71% | 7.78%–96.93% |

Leaving out each sampled date in turn gives attributed-subset top-three shares of 82.45%–93.57%. Top-three membership can change between checks.

The largest attributable trade supplies 42.14% of attributable USD. 78 swaps of at least $1,000 carry 92.74% of all sampled USD. Large trades materially affect the headline. Every exclusion removes complete swaps and recomputes both known and unknown denominators.

## Evidence against a stronger claim

The study covers 48 minutes across eight dates, not continuous activity or a probability sample. The classifier declines ambiguous executions, so missing attribution is partly a method limit. Account aliases may share an operator; counterparties may replace an exiting maker. Neither independent operator concentration nor lost-volume effects are measured. These exclusions were selected after inspecting the sample; they are not confidence intervals.

166 of 260 directed asset pairs appear only once. Sparse pair cells cannot support a reliable pair-level dependency ranking.

## What would change the decision

Authenticated, coverage-audited settlements and independently verified operator mappings could resolve the unknown share. The thesis uses project research gates of at least 90% attributed USD, top-three interval width at most 10 percentage points and HHI width at most 0.05. These are not industry standards or automatic buy signals; fuller disclosure could reveal high concentration.

The actionable conclusion is to keep solver diversification unverified while documenting the observed account exposure. It is not a bearish NEAR price call, a forecast of liquidity loss or a measurement of token-holder value capture.

[All exclusions](data/sensitivity.csv) · [Account recurrence](data/account-persistence.csv) · [Full methodology and thesis](https://github.com/sammy-XXIV/lithium-final/blob/main/THESIS.md)
