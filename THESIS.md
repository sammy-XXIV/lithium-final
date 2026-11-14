# Lithium: the limits of auditing solver dependence

## Claim and investment decision

**Do not credit a solver-diversification premium solely to gross Intents volume.** In a volume-driven investment case, leave diversified and durable solver supply unverified until authenticated settlement coverage and operator mappings support it. This is a negative assessment of a specific underwriting assumption, not a blanket bearish NEAR call or a token-price target.

The measurable baseline is partial account attribution: 28.37% of sampled USD across 15 account IDs. The largest observed account touches 18.30% of all sampled USD, while its 64.48% share of attributable USD is a selected-subset statistic. Use the former as documented sample exposure and the latter as a warning against extrapolating the measured subset. Neither predicts how much activity would disappear if that account stopped filling: competing makers might replace it, and account aliases might share an operator. No maker-exit counterfactual has been measured.

| Underwriting question | Observed baseline | Decision in this study |
| --- | --- | --- |
| Can gross volume establish independent solver diversity? | 71.63% USD unattributed; 15 account IDs are not authenticated independent operators | Do not treat diversity as independently verified |
| Is concentration narrow enough to use as a point estimate? | Top-3 account bounds 25.91–97.53%; HHI 0.0370–0.8122 | Preserve the interval; do not substitute the selected subset's 91.31% top-3 share |
| Does volume establish NEAR token value capture? | No completed revenue-to-token-holder bridge or replacement-capacity analysis | Do not derive a token valuation from these data |
| What would change the assessment? | Project gates: at least 90% attributed USD, top-3 width at most 0.10, HHI width at most 0.05, authenticated operator mapping | Reassess the diversification claim; narrow bounds can still reveal high concentration |

These gates are research choices stated before the corrected attribution analysis, not industry thresholds or automatic investment recommendations. The positive countercase is that independently mapped makers and replacement capacity are diverse despite private settlement. An authorized, coverage-audited disclosure could establish that; the present study cannot reject it. Growth and useful privacy can coexist with robust competition.

## Question and claim

**How much successful 1Click volume can an outsider attribute to executing accounts, and how sensitive is concentration to the unattributed volume?**

Our claim concerns the evidence: where execution is private, public volume alone cannot verify dependence on particular fillers. That limits independent assessment of volume durability. It does **not** establish fragile liquidity, centralization, low competition or a bearish view of NEAR.

The original proposal sought to measure solver concentration directly. The feasibility spike invalidated its proposed shortcut: a repeated public counterparty can be the shared confidential treasury. We changed the measurement question rather than calling that treasury a solver.

## Definitions

- **Volume:** Explorer `amountInUsd` for successful 1Click swaps, counted once per deposit identity. No claim about all Intents activity or fee revenue.
- **Settlement class:** public, confidential treasury or unresolved, based on successful verifier receipts linked to the swap. Missing receipts are unresolved.
- **Attributed account:** a supported executing account in a linked public `token_diff`; the implementation aggregates all token_diff entries in one complete two-account execution, requires every customer entry to match the swap hashes, and checks exact per-token closure including reported protocol fees. Multi-account batches and ambiguous matches remain unknown.
- **Solver/operator:** the economic party operating one or more executing accounts. Account attribution alone does not prove independent operator identities.
- **Coverage:** attributed valid input USD divided by all valid input USD in the sampled scope. Settlement visibility and attribution are different measures.

## Evidence for the auditability concern

The [initial feasibility spike](docs/SPIKE_RESULT.md) inspected five successful swaps and all 19 linked NEAR transactions. Each had origin shielding and destination release through the documented confidential treasury, without public `token_diff` execution. The official [Confidential Intents architecture](https://docs.near-intents.org/integration/market-makers/confidential-intents) places confidential swap execution on FAR, whose settlement details are not visible to public indexers.

This is direct evidence that the public-counterparty shortcut fails for those five swaps. It is not an estimate of how common such swaps are.

The wider collection contains 555 swaps across 24 complete windows and $836,107.521017888862 of input USD, with all 1,333 linked transaction response graphs complete. A classifier audit corrected a version omission and a matcher that mistook token_diff row count for account count. The corrected rule attributes **235 swaps / $237,244.082545028184 / 28.37% of sampled USD to 15 executing account IDs**. It classifies 361 swaps as public (235 attributable, 126 ambiguous), 93 as confidential-treasury paths and 101 as unresolved. The treasury share remains $55,125.52 / 6.59%; the common treasury is never a filler. [Correction and real-receipt audit](docs/ATTRIBUTION_AUDIT.md), [results](docs/RESULTS.md) and [manifest](docs/data/manifest.json).

The final schema review found no unsupported version/event combinations or malformed `EVENT_JSON` logs among successful `intents.near` receipts in the bundled DIP4 scope. All observed versions are already accepted. No additional schema rule or attribution relaxation was justified. Replaying the same pipeline retains the corrected account attribution; the remaining public ambiguity and absent settlement links stay unknown. [Review scope and classification reasons](docs/ATTRIBUTION_AUDIT.md#final-schema-review--2026-11-14).

Within the attributable subset, the largest account represents **64.48%** and the largest three **91.31%** of attributed USD. The largest account's observed contribution is **18.30% of the entire sampled denominator**. These are measurable account-level dependencies in a selected subset, not evidence of independent company concentration or protocol-wide dominance. Account aliases are not merged. The remaining **71.63% of USD is unattributed**, so attributing the subset's concentration to the whole market would be a selection error.

## Does observed dependence survive exclusions?

The leading executing account, `crux-solver.near`, appears in 21 attributable swaps across 7 of the 8 sampled dates and 13 windows. Removing each sampled date in turn gives attributable-subset top-three shares of 82.45–93.57%. This is recurring account involvement within the sample, not evidence of continuous availability or independent operator identity.

Large trades materially affect the headline. One attributable swap supplies 42.14% of attributable USD. Removing it lowers attributable top-three concentration from 91.31% to 84.98%; removing the ten largest attributable swaps lowers it to 71.71%. Removing the ten largest swaps across the full sample instead gives 82.85%. The exclusion rules select different populations and cannot be interchanged.

Every check removes complete swaps, recalculates the remaining denominator and retains all remaining unknown USD. Top-three account membership can change. These are post-hoc descriptive checks, not preregistered tests, sampling intervals or maker-exit counterfactuals. 166 of 260 directed pairs occur once, preventing reliable pair-level dependency rankings. [Computed investment brief](docs/INVESTMENT_BRIEF.md), [exact checks and removed swap IDs](docs/data/sensitivity.json), [account recurrence](docs/data/account-persistence.csv).

## Counterevidence

Public settlement may support attribution for other dates, pairs or sizes. Corrected account attribution already establishes that public attribution is possible for part of this sample. Scope and method qualifications are collected in Limitations.

Confidentiality can serve legitimate privacy requirements. It does not show that the underlying maker population is small, that makers will leave, or that volume is transient. Different public account IDs can share an operator; conversely, the common treasury can serve many independent operators. Both mistakes invalidate simplistic concentration arguments.

## Concentration under unknown attribution

For attributed account volumes a1 ≥ a2 ≥ …, unknown volume U and total T, the dashboard reports concentration within the attributed subset and conservative outer bounds over the full observed valid-USD sample:

- Top-N: `[sum(top N a)/T, min(1,(sum(top N a)+U)/T)]`, for N = 1, 3 and 10.
- HHI on the 0–1 scale: `[sum(a²)/T², ((a1+U)² + sum(other a²))/T²]`.

The upper HHI assigns all unknown volume to the largest known account, or one new account if no account is known. Lower bounds allow divisible unknown volume and arbitrarily many new accounts; they are infima and need not be attainable with this finite set of swaps. These are uncertainty ranges, not sampling confidence intervals. They do not resolve operator identity or bound the unsampled protocol.

If no volume can be attributed, subset concentration is unavailable and the conservative full-sample bounds are [0,1]. That result means the evidence is uninformative about concentration, not that actual concentration is zero or one.

Current model-free full-sample **account** bounds are: top-1 **18.30–89.92%**, top-3 **25.91–97.53%**, and HHI **0.0370–0.8122**. These preserve known account totals and assign all 71.63% unknown USD across possible accounts. They are not verified operator bounds: several known IDs could belong to one operator.

As a separate sensitivity case, assume every sampled swap is one indivisible filler execution. Preserve all known account totals and assign each unknown swap to a distinct account for the lower bound. This gives top-1 **25.92–89.92%**, top-3 **49.97–97.53%**, HHI **0.1156–0.8122**. The one-swap/one-filler premise is not established by these receipts.

## Due-diligence use

Lithium is intended to help an analyst decide whether a solver-diversification claim is supported by public evidence, or whether authenticated settlement disclosures and independent operator mappings are needed before relying on it. The current verdict is partial account attribution with unverified operator independence. The attributable subset has measurable account concentration, but its selection and the unknown share prevent a protocol-wide solver conclusion. User adoption and actual decision impact remain unvalidated.

The dashboard's separate disclosure scenario asks what additional authenticated coverage could change. Inputs represent hypothetical, disjoint full-denominator shares assigned to independent operators, with the remainder unknown. They are not evidence that disclosures occurred. Top-1, top-3 and HHI bounds narrow according to the entered shares; full disclosure may reveal high concentration. This scenario neither changes the observed sample nor authenticates private settlement records.

## Breaking points

A completed, independently checked analysis with at least 90% of valid sampled USD attributable would weaken the practical auditability concern for that sampled scope. Full-sample top-3 bound width at most 0.10 and HHI bound width at most 0.05 would make concentration more informative. These are stated decision criteria, not current findings or forecasts; they were set after the spike and Explorer collection, before a completed wider receipt analysis.

Verified evidence of low or falling operator concentration would strengthen the case for diversified filling. A lack of volume disruption during independently established maker exits would weaken a fragility hypothesis. Neither is established by this study's current data. No exit counterfactual, prediction or token-return forecast is being presented as an observed outcome.

Apply the [explicit condition/verdict table](README.md#breaking-points). The coverage and width gates plus authenticated mappings reopen the auditability assessment; they do not award a diversification premium. Full sampled-USD coverage and verified mappings for every executing account would support measuring operator concentration after merging aliases. A mapping proving shared ownership changes the interpretation of separate account IDs even if attributable USD is unchanged. If independently verified replacement settlements cover all exposed flow at unchanged captured-fee yield during a documented departure, the model's no-replacement loss scenario is contradicted for that event. These are conditional breaking points, not completed disclosures, verified exits or forecasts.

## What data would settle the unknowns

### What an analyst should demand

Use the [request/source/scenario checklist](README.md#what-an-analyst-should-demand) before changing an underwriting assumption:

- [ ] Obtain signed settlement linkage from the settlement maintainers and authorized FAR record holders; reconcile amounts to the sampled denominator before raising assumed attribution.
- [ ] Obtain independently corroborated ownership and alias disclosures from makers; group accounts into economic operators before entering disclosure shares.
- [ ] Obtain complete coverage and omitted-record accounting from the export and Explorer maintainers; leave every undisclosed share unknown.
- [ ] Obtain wallet-level fee/captured-revenue reconciliation from revenue-wallet stewards and dataset maintainers; update the cited fixed economic inputs only with reproducible evidence.
- [ ] Obtain independently documented departures and comparable before/during/after observations from makers, integrators and operations; test volume and departures separately from replacement.

The disclosure calculator accepts hypothetical operator shares. Revenue departures remain account-based, and the revenue model has no replacement control. Neither calculator authenticates the requested records.

For confidential swaps, an authorized and verifiable FAR record must connect each Explorer swap identity and intent hash to executed account deltas, amounts and timestamps. Independent operator mappings are additionally needed for company-level concentration. Disclosure coverage matters: a selective export cannot justify assigning the remaining unknown volume.

Public NEAR receipts in BigQuery do not by themselves reveal private FAR execution. We have now discovered the live schemas, dry-run and executed a partition-filtered verifier event inventory across all 24 sampled windows. The warehouse returned 9,280 logs on SUCCESS_VALUE outcomes, 359 on FAILURE outcomes and 11 on SUCCESS_RECEIPT_ID outcomes. Successful-value groups include 1,671 `intents_executed` logs and 1,460 `token_diff` logs. These are event counts, not swaps or attributed solvers. Continuation outcomes do not themselves establish downstream completion, and failed logs do not establish transfers. No warehouse-to-Explorer swap reconciliation is claimed, and the attribution bounds are unchanged. [Executed SQL](queries/02_sample_window_event_inventory.sql), [results](queries/results/02_sample_window_event_inventory.json) and [job metadata (identity fields removed)](queries/results/02_sample_window_event_inventory.job.json) document the independent public-activity audit.

## Reproduce

Run `make reproduce`, or `python tools/reproduce_tables.py` without make, to regenerate all published analytical tables/charts from `docs/data` and print PASS/FAIL against every summary field and generated file. Open `reproduced/from-data/index.html`. Separately, `python tools/reproduce.py` replays attribution from the bundled credential-free receipt snapshot and approved configuration. Neither command collects new data. Every generated chart ships its computation, denominator, CSV and linked evidence. [Scope and commands](docs/RESEARCH_GUIDE.md).

## Conditional revenue durability scenarios

The dashboard now models account exits rather than claiming observed lost revenue. Let c be assumed attributable USD coverage and s the departing observed accounts' share within attributable volume. With at least one departure, exposed share ranges from c*s to c*s+(1-c); no departures imply zero exposure. Missing volume may belong entirely to those accounts or elsewhere. Moving c keeps the observed within-attributed account distribution fixed.

We scale sample USD and separately cited annualized economics by the chosen volume factor, then apply those exposure extremes. Remaining captured revenue is the external input times the volume factor times one minus exposed share. The [pinned external inputs](data/inputs/economic-baseline.json) are Andrea Soldano's near-thesis Q5, snapshot 2026-10-31: $70.24M/year gross fees and $19.19M/year captured revenue, annualized from 90 days. Lithium has not independently reconciled those values. Affiliate fees are not NEAR captured revenue. No external code, prose or document structure is incorporated.

Andrea Soldano's [valuation discussion in the pinned thesis file](https://github.com/soldanoandrea/near-thesis/blob/13b580f37e97d04fa0403f5c1a785f962886bddd/thesis/THESIS.md#valuation-ranges-and-priors-not-a-price-target) shows why the revenue definition and issuance burden matter to the investment case. Lithium contributes a narrower evidence test beneath that argument: how much confidence account-level settlement records can support in diversified, durable solver supply. The Q5 figures and source SHA-256 were verified against that file; this is citation verification, not an independent reconstruction of its economics. The valuation argument is credited without adopting its code, writing or document structure.

The model assumes no replacement. A positive modeled lower loss bound is not a minimum actual loss: replacement can reduce actual loss to zero. Detailed assumptions and scope follow.

## Limitations

- **Sample selection and composition.** [sampling.json](sampling.json) predeclares eight dates from 2026-09-16 to 2026-11-11, three UTC slots and two minutes per slot: 24 windows and 48 minutes. This is a convenience sample, not a population census or continuous observations across those dates. The initial five-swap spike covers roughly 40 seconds and is not representative. Pair/size composition and time-of-day can confound aggregate changes; empty cells do not establish zero confidential share. Invalid USD is excluded and counted, while unknown identities remain in the valid-USD denominator.
- **Classifier and missing evidence.** The rule declines ambiguous multi-account flows and requires exact two-account fee-adjusted closure. Unsupported schemas, ambiguity and absent settlement linkage are separate from confidential execution. The superseded zero-attribution result partly reflected a missing intents_executed 0.3.1 schema and a restrictive two-row/zero-fee matcher; it is not evidence that public attribution is impossible. RPC failures are reported separately. An initial provider refused archival access; a working provider subsequently supplied all 1,333 complete linked transaction graphs. Complete public graphs do not recover private FAR execution or guarantee identifiable counterparties.
- **Identity and selection.** Account IDs are not verified companies or independent operators; aliases may share ownership. A shared treasury may serve many independent operators and is never counted as one solver. The selected attributable subset cannot describe the unknown share or the unsampled protocol. Privacy alone does not demonstrate concentrated operators, fragile liquidity or transient volume.
- **Bounds and exclusions.** Model-free bounds allow divisible unknown USD and arbitrarily many new accounts; their lower endpoints can be unattainable infima with finite swaps. The indivisible one-swap/one-filler scenario is unverified. Bounds and post-hoc trade/date exclusions are not confidence intervals, preregistered tests, maker-exit counterfactuals or forecasts. Sparse pair cells do not support reliable pair-level dependency rankings.
- **Distribution and economics.** Referral and fee-recipient incidence are secondary distribution evidence; recipients can overlap and total shares can exceed 100%. Routed USD is not fee revenue. External gross fees include affiliate fees and differ from NEAR captured revenue. The cited annualized economics have not been independently reconciled by Lithium and have a different time period and denominator from this sample. Token-holder capture, buybacks, value accrual and causal links to token valuation are not established here.
- **Warehouse interpretation.** BigQuery is a separate public event inventory, without warehouse-to-Explorer swap reconciliation or private-filler identification. Event logs are not swaps or operators. Failed logs do not establish transfers; continuation outcomes alone do not establish downstream completion. Warehouse evidence does not alter the account-attribution bounds.
- **Scenarios and controls.** Revenue scenarios assume the sampled account mix applies to revenue-bearing activity, constant fee yield and capture, and no replacement/rerouting. Moving assumed attribution retains observed account weights. Revenue departures count accounts, not mapped operators; aliases are not automatically merged and there is no replacement-rate control. Actual loss can be zero after replacement, even when a conditional modeled lower endpoint is positive. Disclosure scenarios assume authenticated, independent operators with disjoint full-denominator contributions; a hypothetical input establishes no actual disclosure and leaves the observed data unchanged. Full coverage can reveal high concentration. Remaining revenue is a scenario, not verified durability, a prediction or a token valuation.
- **Stress and adoption.** The 24 short, nonconsecutive windows establish neither a volatile week nor an independently documented solver exit. There is no continuous before/during/after volume and fee series; absence in a short window is not evidence of departure. Trade/date exclusions are sensitivity checks, not historical stress-event results. [Stress assessment](docs/data/stress-evaluation.json). User adoption and actual investment-decision impact remain unvalidated.
- **Reproduction boundary.** The data-only build trusts published classifications, pseudonymous swap IDs and provider evidence; it checks arithmetic and presentation. The separate bundled-snapshot replay reruns the classifier and deposit-identity hashing. Neither independently authenticates confidential settlements. Additional archived collection is excluded and is not resumed. Not financial advice.
