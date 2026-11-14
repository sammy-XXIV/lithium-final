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

Dollar scenarios use separately credited external annualized inputs. They assume no replacement; replacement can reduce actual loss to zero. **Scenarios, not predictions.** See the source paragraph below and the consolidated assumptions in Limitations.

## What follows from the evidence?

Do not infer independent solver diversification from gross swap volume. The largest observed account represents **18.30% of sampled USD**, recurring on **7 of 8 sampled dates**. The attributable subset's top-three share is **91.31%**, but that selected subset cannot describe the unknown volume. Large-trade and date exclusions are [computed separately](docs/data/sensitivity.csv).

## Limitations

- **Sampling and stress:** 24 two-minute windows, 48 minutes on eight nonconsecutive dates; a convenience sample, not continuous days or a protocol-wide census. No volatile week, documented solver exit or continuous before/during/after volume and fee series is established. An account missing from a short window is not a verified exit. [Stress assessment](docs/data/stress-evaluation.json).
- **Method and visibility:** attribution requires supported schemas, matching intent hashes and exact two-account fee-adjusted token closure. Ambiguous executions remain unknown, so missing attribution partly reflects the method. Confidential settlement and unlinked executions limit visibility; the common treasury is never labeled a solver. The old zero-attribution result was corrected using the same evidence. The final [schema review](docs/ATTRIBUTION_AUDIT.md#final-schema-review--2026-11-14) found no remaining unsupported version/event combinations in the bundled successful DIP4 logs; 126 public swaps remain ambiguous and 101 have no linked settlement. No new schema rule was added.
- **Identity and bounds:** account IDs can be aliases; independent operators and maker replacement are unverified. The attributable subset cannot stand in for unknown volume. Model-free lower bounds allow divisible unknown USD and arbitrarily many accounts; they can be unattained infima. The separate one-swap/one-filler scenario is unverified. These are uncertainty ranges, not confidence intervals.
- **Fees and sources:** Explorer USD values and public RPC records underpin the analysis. Referral/app-fee parameters are not measured USD fee revenue; BigQuery is an independent event inventory, not swap-level reconciliation or private FAR attribution. External gross fees include affiliate fees and differ from captured revenue. The cited annualized inputs have not been independently reconciled by Lithium and have a different period and denominator from this sample. Token-holder value capture, buybacks and a token valuation are not established here.
- **Scenario assumptions:** no replacement/rerouting, constant fee yield and capture, and unverified application of the sampled account mix to revenue-bearing activity. Moving assumed attribution retains observed account weights. Actual lost revenue can be zero after replacement. Departures count accounts; authenticated operator mappings do not automatically regroup them, and there is no replacement-rate control. Disclosure entries assume independent operators, disjoint full-denominator shares and authenticated records; entering them authenticates nothing. Full disclosure can reveal high concentration.
- **Interpretation and reproducibility:** hypothetical disclosures and post-hoc trade/date exclusions are not forecasts or observed solver-exit effects. The data-only command checks arithmetic and presentation from shipped classifications; the separate receipt replay checks their derivation from the bundled public responses. Neither authenticates private settlements. Additional archived collection is excluded. User adoption and actual investment-decision impact remain unvalidated. Not financial advice.

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

Andrea Soldano's [near-thesis valuation argument](https://github.com/soldanoandrea/near-thesis/blob/13b580f37e97d04fa0403f5c1a785f962886bddd/thesis/THESIS.md#valuation-ranges-and-priors-not-a-price-target) makes the treatment of Intents revenue central to NEAR's valuation while testing whether value capture can offset issuance. Lithium examines one assumption beneath revenue durability: whether public settlement evidence verifies diversified solver supply. Its revenue scenarios use that same pinned file's Q5 published inputs of **$70.24M annualized gross fees and $19.19M annualized captured revenue**, measured over the trailing 90 days as of 2026-10-31. The figures and file hash were checked against the source; this verifies the citation, not the underlying economics. [Source hash, units and assumptions](data/inputs/economic-baseline.json). Credit is for the valuation argument and numeric inputs; no external code, prose or structure was copied.

[Executed BigQuery SQL and provenance](queries/02_sample_window_event_inventory.sql) · [Classifier correction and real-receipt audit](docs/ATTRIBUTION_AUDIT.md) · [Snapshot custody](snapshots/README.md)

Own project code: [MIT](LICENSE).
