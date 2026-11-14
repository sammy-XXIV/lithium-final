# Lithium

**Public receipts attribute 28.37% of $836,107.52 across 555 sampled NEAR Intents swaps to 15 executing accounts; the full-sample top-three account share remains 25.91–97.53%.**

Lithium tests whether public evidence supports diversified, durable solver supply behind NEAR Intents revenue. **71.63% of sampled USD remains unattributed.** Executing accounts are not verified independent operators; solver dependence cannot be fully audited from these public records.

[Dashboard](https://sammy-xxiv.github.io/lithium-final/) · [Investment thesis](THESIS.md) · [Short brief](docs/INVESTMENT_BRIEF.md) · [Methods](docs/RESEARCH_GUIDE.md)

## What an analyst should demand

Before relying on a solver-diversification claim, request:

- **Settlement links:** authenticated swap/intent IDs tied to executed account deltas and amounts, including confidential settlement.
- **Operator mappings:** evidence connecting executing accounts to independent operators, with aliases disclosed.
- **Coverage and economics:** complete denominators, missing-volume explanations and reconciled fees versus captured revenue.
- **Continuity evidence:** comparable volume, fees and execution records before, during and after a documented maker departure, including replacement activity.

Use the dashboard to test assumptions while these are missing; do not treat gross volume as proof of diversified solver supply.

## Reproduce offline

With Python 3.11+, from a fresh clone, run `python tools/reproduce.py`. No package installation, credentials or network is required. The committed snapshot includes all 555 swaps and 1,333 complete linked transaction graphs.

| Do X | See Y |
| --- | --- |
| `python tools/reproduce.py` | Hash checks, all published summary fields and sensitivity checks verified |
| Open `reproduced/docs/index.html` | Static dashboard, charts, evidence tables and arithmetic check; works directly from disk |
| Open `docs/data/swaps.csv` | All sampled swaps, classification reasons, amounts and transaction links |
| Open `docs/INVESTMENT_BRIEF.md` | Account recurrence, trade/date exclusions and uncertainty |
| `python -m pip install -e .` then `python -m unittest discover -s tests` | Research regression checks; installation is optional for reproduction |

## Interactive durability scenarios

Open the dashboard's durability section and vary assumed attribution, departures among the largest observed accounts, and volume change. It reports sample-scope volume exposure, annualized gross fees and captured revenue at risk, and a remaining-revenue range. Unknown attribution stays in both endpoints. The historical slice ranges and the absence of verified exits are shown beside the controls.

Fee/revenue dollar scenarios use [near-thesis Q5](https://github.com/soldanoandrea/near-thesis/blob/13b580f37e97d04fa0403f5c1a785f962886bddd/thesis/THESIS.md#q5-fees-and-the-take-rate): **$70.24M gross fees and $19.19M captured revenue**, trailing 90 days annualized as of 2026-10-31. These are external published inputs, not Lithium measurements. [Citation and assumptions](data/inputs/economic-baseline.json).

The model assumes no replacement/rerouting, constant fee yield and that the sample account mix applies to revenue-bearing activity. Moving attribution retains observed account weights. Actual lost revenue can be zero if activity is replaced. **Scenarios, not predictions. Not financial advice.**

## What follows from the evidence?

Do not infer independent solver diversification from gross swap volume. The largest observed account represents **18.30% of sampled USD**, recurring on **7 of 8 sampled dates**. The attributable subset's top-three share is **91.31%**, but that selected subset cannot describe the unknown volume. Large-trade and date exclusions are [computed separately](docs/data/sensitivity.csv).

## Limitations

- **Sampling:** 24 two-minute windows, 48 minutes on eight dates; a convenience sample, not continuous days or a protocol-wide census.
- **Method:** attribution requires supported schemas, matching intent hashes and exact two-account fee-adjusted token closure. Ambiguous executions remain unknown, so missing attribution partly reflects the method.
- **Hidden activity:** confidential settlement and unlinked executions limit visibility. The common treasury is never labeled a solver.
- **Identity:** account IDs can be aliases; independent operators and maker replacement are unverified.
- **Fees and sources:** Explorer USD values and public RPC records underpin the analysis. Referral/app-fee parameters are not measured USD fee revenue; BigQuery is an independent event inventory, not swap-level reconciliation.
- **Scenarios:** hypothetical disclosures and exclusions are not predictions, confidence intervals or observed solver-exit effects. Not financial advice.

## Evidence against the claim; what would change it?

Private settlement can coexist with diverse, competitive makers. Public attribution is possible for part of the sample, and another maker could replace an exiting account. No causal connection from an account's departure to lost revenue is established. An authenticated settlement export with broad coverage, independent operator mapping and observed continuity through documented exits would make the diversification and durability case testable. See the [thesis](THESIS.md) for explicit research gates and counterevidence.

## Prior work and related research

The [Vox interface](https://github.com/sammy-XXIV/vox) was first built for another hackathon. Lithium builds on that prior interface work for presentation. New for NEAR: Explorer collection, receipt linkage and fee-netted attribution, committed evidence snapshots, USD coverage and account-concentration bounds, sensitivity analysis, an uncertainty-aware durability scenario view, BigQuery event inventory and the investment thesis. The static interface includes no voice, live agent or API-key feature.

The closest related entry is [Andrea Soldano's near-thesis](https://github.com/soldanoandrea/near-thesis), a broader NEAR usage, revenue, dilution and valuation study. Lithium focuses on executing-account attribution and the uncertainty around solver dependence. External figures, when used, are identified separately from Lithium's measurements. Its code, prose and structure are not incorporated.

[Executed BigQuery SQL and provenance](queries/02_sample_window_event_inventory.sql) · [Classifier correction and real-receipt audit](docs/ATTRIBUTION_AUDIT.md) · [Snapshot custody](snapshots/README.md)

Own project code: [MIT](LICENSE).

## Real stress event: not established

The current 24 short, nonconsecutive windows do not identify a volatile week or independently documented solver exit. There is no continuous before/during/after volume and fee series. Missing an account in a two-minute window is not evidence that it left the market. The trade/date exclusions are sensitivity analyses, not historical stress-event results. [Scope and assessment](docs/data/stress-evaluation.json).
