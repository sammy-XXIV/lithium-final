# Lithium

**Solver diversification remains unverified. Public receipts attribute 235 of 555 sampled swaps to 15 executing account IDs; those IDs are not verified independent operators.**

Discount any investment thesis relying on diversified, durable solver supply until authenticated settlement links, operator mappings and full disclosure coverage support it. Lithium makes the observed account exposure and the effect of missing evidence reproducible.

[Disclosure calculator](https://sammy-xxiv.github.io/lithium-final/#decision) · [Revenue scenarios](https://sammy-xxiv.github.io/lithium-final/#durability) · [Investment thesis](THESIS.md)

| Do X | See Y |
| --- | --- |
| Run `make reproduce` or `python tools/reproduce_tables.py` | PASS/FAIL for every summary field and regenerated analytical table/chart; open `reproduced/from-data/index.html` |
| Enter operator shares in the disclosure calculator | How hypothetical coverage changes concentration bounds |
| Vary attribution, departures and volume in revenue scenarios | Conditional exposure and remaining revenue ranges |
| Run `python tools/reproduce.py` | Replay attribution from the original bundled receipts for the same 555 swaps |

[Sample evidence](docs/data/swaps.csv) · [Exact figures](docs/data/summary.json) · [Short brief](docs/INVESTMENT_BRIEF.md) · [Methods](docs/RESEARCH_GUIDE.md)

## What an analyst should demand

| Request and verify | Request from | Calculator scenario it changes |
| --- | --- | --- |
| ☐ Authenticated swap/intent IDs linked to executed account deltas, amounts and timestamps, including confidential settlement | NEAR Intents/1Click settlement maintainers and authorized FAR record holders; independently check signatures and linkage | Disclosure shares; revenue scenario's assumed attribution, after reconciling sampled USD |
| ☐ Signed account ownership, aliases and independently checked account-to-operator mappings | Each participating maker/operator, corroborated by a reviewer independent of that operator | Group aliases before entering hypothetical operator shares in the disclosure calculator |
| ☐ Complete export scope, total USD denominator, omitted records and explanations for unmatched volume | Explorer/1Click data maintainers and the settlement export provider | Disclosure calculator's unknown remainder; never treat selective disclosures as full coverage |
| ☐ Gross-fee versus captured-revenue reconciliation, wallet inflows and measurement period | Revenue-wallet stewards and the maintainers of the cited economics dataset | Revenue scenarios' annualized fee/revenue baseline; a sourced rebuild is required to change these fixed inputs |
| ☐ Dated maker departure plus comparable volume, fees and replacement activity before, during and after it | Departing maker, affected integrators and NEAR Intents operations; independently corroborate the event | Revenue scenario's departures and volume change; replacement evidence tests the model's no-replacement assumption |

Use the [disclosure calculator](https://sammy-xxiv.github.io/lithium-final/#decision) and [revenue scenarios](https://sammy-xxiv.github.io/lithium-final/#durability) to test assumptions while these are missing. Revenue departures count observed accounts; operator mappings do not automatically regroup those account weights. The current model has no replacement-rate control. A hypothetical entry never updates the observed measurements.

## Reproduce offline

With Python 3.11+, run `make reproduce` (or `python tools/reproduce_tables.py` without make). This regenerates every published analytical table/chart from `docs/data`, prints PASS/FAIL against every summary field and generated file, and exits nonzero on a mismatch. No package installation, credentials or network is required. Open `reproduced/from-data/index.html`.

For a separate replay of account attribution from original receipts, run `python tools/reproduce.py`. The committed snapshot includes all 555 swaps and 1,333 complete linked transaction graphs. The data-only build takes classifications as inputs; the receipt replay verifies how they were derived. Archived extra collection and historical audit records are provenance inputs, not newly measured results.

With the package installed, `python -m unittest discover -s tests` runs the research regression checks. Installation is optional for both reproduction commands; `PYTHONPATH=src` also supports the tests.

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

## Breaking points

| Evidence condition | Change to the verdict |
| --- | --- |
| Independently checked attribution covers at least 90% of valid sampled USD, full-sample top-three bound width is at most 0.10, HHI bound width is at most 0.05, and authenticated operator mappings cover the attributed accounts | Reassess the practical auditability concern for this sample. These existing project gates reduce uncertainty; they do not prove low concentration. |
| Authenticated settlements account for all sampled valid USD and every executing account has a verified operator/alias mapping | Replace an unverified operator-concentration assessment with a measured one for the sample, after merging aliases. It may reveal concentration rather than diversification. |
| A verified mapping shows that distinct observed account IDs share an operator | Revise the identity interpretation and recompute operator-level concentration separately. Keep the published account-level result labeled as such. |
| During an independently documented departure, replacement executions settle all exposed flow at unchanged captured-fee yield | The no-replacement revenue-loss scenario does not describe that event; lost captured revenue from that replaced flow is zero under these stated conditions. It does not establish future replacement capacity. |

The coverage and width gates were stated before the corrected wider receipt analysis. They are research decision criteria, not industry standards, current achievements or buy signals. Test their concentration consequences in the [disclosure calculator](https://sammy-xxiv.github.io/lithium-final/#decision). No binding settlement export, operator mapping or documented exit is claimed here.

Private settlement can coexist with diverse, competitive makers. Public attribution is possible for part of the sample, and another maker could replace an exiting account. No causal connection from an account's departure to lost revenue is established. An authenticated settlement export with broad coverage, independent operator mapping and observed continuity through documented exits would make the diversification and durability case testable. See the [thesis](THESIS.md) for explicit research gates and counterevidence.

## Prior work and related research

The [Vox interface](https://github.com/sammy-XXIV/vox) was first built for another hackathon. Lithium builds on that prior interface work for presentation. New for NEAR: Explorer collection, receipt linkage and fee-netted attribution, committed evidence snapshots, USD coverage and account-concentration bounds, sensitivity analysis, an uncertainty-aware durability scenario view, BigQuery event inventory and the investment thesis. The static interface includes no voice, live agent or API-key feature.

The closest related entry is [Andrea Soldano's near-thesis](https://github.com/soldanoandrea/near-thesis), a broader NEAR usage, revenue, dilution and valuation study. Lithium focuses on executing-account attribution and the uncertainty around solver dependence. External figures, when used, are identified separately from Lithium's measurements. Its code, prose and structure are not incorporated.

[Executed BigQuery SQL and provenance](queries/02_sample_window_event_inventory.sql) · [Classifier correction and real-receipt audit](docs/ATTRIBUTION_AUDIT.md) · [Snapshot custody](snapshots/README.md)

Own project code: [MIT](LICENSE).

## Real stress event: not established

The current 24 short, nonconsecutive windows do not identify a volatile week or independently documented solver exit. There is no continuous before/during/after volume and fee series. Missing an account in a two-minute window is not evidence that it left the market. The trade/date exclusions are sensitivity analyses, not historical stress-event results. [Scope and assessment](docs/data/stress-evaluation.json).
