# Research evidence and reproduction

[Project summary](../README.md) · [Investment thesis](../THESIS.md)


## The due-diligence decision

**Intended user:** an analyst or protocol risk analyst assessing reliance on swap fillers. **Decision:** whether to rely on a diversification claim or request stronger evidence. **Action supported:** identify missing authenticated settlement links, operator mappings and disclosure coverage, then assess how unknown volume limits concentration conclusions. Actual user adoption or changed investment decisions have not been demonstrated.

The disclosure calculator models a separate hypothetical dataset: each percentage is one assumed independent operator's disjoint contribution to the entire sampled USD denominator. Remaining volume stays unknown. It uses the same model-free top-N/HHI formulas as the research, allows arbitrary splitting of unknown volume, and does not modify the observed results. Full disclosure can establish high concentration; narrower bounds do not automatically mean diversification. No synthetic disclosure establishes that a solver actually filled any trade.

| Evidence or scenario | Attributed / assumed disclosed USD | Top-3 range | HHI range (0–1) |
| --- | ---: | ---: | ---: |
| Observed executing accounts under our method | 28.37% attributable | 25.91–97.53% | 0.0370–0.8122 |
| Hypothetical: 20 independent operators, 4.5% each | 90% assumed disclosed | 13.5–23.5% | 0.0405–0.0595 |
| Hypothetical: independent operators at 70%, 10%, 10% | 90% assumed disclosed | 90–100% | 0.5100–0.6600 |

The two examples illustrate why **coverage and concentration are different questions**. They are calculator outputs under stated assumptions, not observations about real solvers.

[Open the disclosure calculator](index.html#decision).

Run its mathematical boundary checks with `node tools/check-disclosure.cjs`. It works entirely in the browser, including the standalone offline dashboard, and sends no scenario inputs to a server.

## The finding: volume does not identify its fillers

The original hypothesis was that repeated public counterparties could reveal solver concentration. An initial [five-swap spike](SPIKE_RESULT.md), covering all 19 linked transactions, found that the repeated counterparty was a **shared confidential treasury**. Treating it as one solver would manufacture a concentration result.

We changed the question: **how much volume can this public evidence attribute, and what concentration remains consistent with the unknowns?**

NEAR's [Confidential Intents architecture](https://docs.near-intents.org/integration/market-makers/confidential-intents) documents the shared public treasury and private FAR execution. The treasury identifies infrastructure serving participants; it does not identify one economic solver.

The wider sample contains **555 successful swaps, $836,107.52 in input USD and 1,333 linked NEAR transaction hashes**. All linked response graphs are complete. Corrected rules attribute **235 swaps and $237,244.08 (28.37% of valid sampled USD) to 15 executing account IDs**. These are not verified independent operators.

| Settlement evidence | Swaps | Input USD | Share of sampled USD |
| --- | ---: | ---: | ---: |
| Public settlement (235 attributable; 126 ambiguous) | 361 | $449,619.09 | 53.78% |
| Linked confidential-treasury path | 93 | $55,125.52 | 6.59% |
| Unresolved under current rules | 101 | $331,362.92 | 39.63% |
| **Total** | **555** | **$836,107.52** | **100%** |

Source: [swap-level CSV](data/swaps.csv), [exact summary](data/summary.json), [receipt evidence](data/evidence.json), [query parameters](data/queries.json), [provenance manifest](data/manifest.json). Percentages are rounded independently.

**The original zero-attribution headline was partly a tooling defect.** We corrected missing support for intents_executed 0.3.1 and aggregate complete two-account executions, including intermediary tokens and reported fees. Every token must balance exactly after fees. The 126 remaining ambiguous public swaps involve unsupported attribution structures, while 101 swaps lack linked settlement evidence. Privacy does not explain every unknown. See the [full correction and real-receipt audit](ATTRIBUTION_AUDIT.md).

The final bundled-schema inventory found no remaining unsupported version/event combinations in successful `intents.near` DIP4 logs. The observed 0.3.0, separately versioned 0.3.1 `intents_executed`, and 0.4.3 events are already supported. No new parser rule was added; attribution remains 235 of 555 swaps. This does not assert support for every protocol schema outside the bundle. [Final schema-review scope](ATTRIBUTION_AUDIT.md#final-schema-review--2026-11-14).

Run `python3 tools/check_attribution_audit.py` to execute the frozen historical attribution function and the current function on the same hash-checked snapshot. It reproduces the zero-to-235 correction and checks the worked receipt's exact fee-adjusted token arithmetic. The [audit](ATTRIBUTION_AUDIT.md) names the defects, transaction, receipt, intent and executing accounts, and distinguishes archived source provenance from independent verification. Regression tests also reject a changed token unit and a third participant in that real receipt.

[Open the observed attribution coverage](index.html#coverage).

### What the bounds establish

| Metric | Public-evidence outer range | Conditional: each swap is one indivisible fill |
| --- | ---: | ---: |
| Top-1 account share | 18.30–89.92% | 25.92–89.92% |
| Top-3 account share | 25.91–97.53% | 49.97–97.53% |
| HHI, on a 0–1 scale | 0.0370–0.8122 | 0.1156–0.8122 |

Observed ranges concern executing account IDs; hypothetical examples separately assume verified independent operators. The outer ranges allow divisible unknown volume and arbitrarily many accounts. Their lower endpoints are infima. The conditional scenario assigns each unattributed swap to a separate account for maximum dispersion, or combines unknown volume for maximum concentration. **The receipts do not establish one filler per swap**, so that scenario is sensitivity analysis rather than measured concentration.

The investment-thesis implication is limited and useful: sampled gross volume alone cannot verify diversified filling or durable dependence on particular market makers. This study does not establish centralized operators, fragile liquidity or a token-price forecast. Narrower bounds would require more supported attribution, authenticated confidential-fill records and mappings from accounts to independent operators. [Full argument and counterevidence →](../THESIS.md)

### Sampling limits

The [declared scope](../sampling.json) is eight dates, three fixed UTC slots per date, and two minutes per slot: **24 windows and 48 minutes total**. It is a convenience sample, not continuous activity across eight weeks or a protocol-wide estimate. USD uses valid, nonnegative Explorer `amountInUsd`; settlement visibility and filler attribution are separate fields. Referral and fee-recipient charts measure distribution relationships, not solver concentration or fee revenue.

## Run and verify

### Static dashboard

Open `docs/index.html` directly from disk. There is no server, wallet or API-key feature in the interface. Optional local HTTP viewing: `python -m http.server 8081 --directory docs`.

### Research checks

Requires Python 3.11+. The application has no Python runtime dependencies. Run from the repository root:

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
```




### Rebuild or fetch the research

For the offline analytical build, run `make reproduce`, or `python tools/reproduce_tables.py` on systems without make. It reconstructs all analytical tables, sensitivity checks, warehouse tables, charts, model inputs, results and the investment brief from `docs/data`; it prints PASS/FAIL for every summary field and generated file. Output is `reproduced/from-data/index.html`. It reuses the existing arithmetic and renderer without changing classifications or the denominator. JSON object order in the embedded model is canonicalized so source-file key order cannot change the generated page. Transport CRLF/LF differences are normalized for comparison; other bytes must match.

This is an arithmetic and presentation check. It trusts the shipped classifications, pseudonymous swap IDs and receipt evidence; it cannot independently authenticate private settlements or recover deposit identities. The separate snapshot replay below reruns the classifier and deposit-identity hashing. Historical audit and excluded extra-collection files remain provenance inputs and are not reclassified or expanded by either command. CI starts from a clean checkout, runs both offline commands, regression tests and the Pages browser checks. No local cache or credentials are restored.

A fresh clone includes all 555 baseline swaps and all 1,333 transaction response graphs in a sanitized, hashed snapshot. With Python 3.11+, no package installation, credentials or network:

```sh
python tools/reproduce.py
```

This checks archive/member hashes, reruns the classifier and analysis, compares every published summary field and writes `reproduced/docs/index.html`. RPC chain result objects are unchanged; transport metadata contains only public provider origins. See [snapshot provenance](../snapshots/README.md). The original private raw cache is still gitignored.

For maintainers with the original complete local cache, `python -m solverline.rebuild --offline` regenerates the published docs.

This strict command fails clearly when raw inputs are missing. To fetch or resume the declared scope, configure `.env` using [.env.example](../.env.example), with an Explorer JWT and a working NEAR mainnet archival RPC:

```sh
python -m solverline.rebuild --fetch --allow-partial
```

Requests are cached, sequential and separated by at least 5.2 seconds. A fresh 1,333-hash receipt run takes at least roughly two hours; retries add time. Keys and raw credentialed RPC responses stay local. The original Python module name `solverline` is retained in commands.

## BigQuery: public event inventory across all 24 windows

We discovered the live schemas and executed partition-filtered SQL against `bigquery-public-data.crypto_near_mainnet_us.execution_outcomes` in **us-east1**. The query inventories `EVENT_JSON:` logs executed by `intents.near` in the eight sampled dates' three two-minute windows. It returned **263 grouped rows across all 24 windows**.

| Execution outcome status | Event logs |
| --- | ---: |
| SUCCESS_VALUE | 9,280 |
| FAILURE | 359 |
| SUCCESS_RECEIPT_ID | 11 |

The SUCCESS_VALUE groups include **1,671 `intents_executed` logs** and **1,460 `token_diff` logs**. These are **event counts, not swap counts, USD volume or solver identities**. Group-specific distinct receipts overlap across event types. Failure logs do not establish completed transfers; SUCCESS_RECEIPT_ID can indicate a continuation whose downstream completion is not checked here.

This warehouse audit covers all verifier activity in those windows, **not a joined reconciliation of the 555 Explorer swaps**. It leaves the existing attribution results unchanged. Nonempty windows do not establish full indexing, and 48 sampled minutes do not establish a protocol-wide trend.

Job **`lithium_windows_20261113T152520Z`** completed with cacheHit false: **12,748,608,695 bytes processed**, **12,749,635,584 bytes billed**, eight daily partitions, below a **16 GiB** maximum. The query was dry-run before execution. Original SQL, results and job metadata (identity fields removed) were imported from the user's authenticated Cloud Shell download; published import hashes preserve the files used for the chart.

[Executed SQL](../queries/02_sample_window_event_inventory.sql) · [Raw results](../queries/results/02_sample_window_event_inventory.json) · [Job metadata (identity fields removed)](../queries/results/02_sample_window_event_inventory.job.json) · [Window CSV](data/bigquery/windows.csv) · [Discovery and reproduction](../queries/README.md)

## Completion and remaining work

| Deliverable | Status |
| --- | --- |
| Public receipt collection for the declared sample | Complete: 555 swaps, 1,333 transaction response graphs |
| Coverage, bounds, evidence downloads and browser arithmetic | Implemented and published |
| BigQuery event inventory | Executed and integrated: all 24 windows, SQL, results, chart and job metadata (identity fields removed) |
| BigQuery swap-level reconciliation / private filler identity | Not established; warehouse event counts do not recover FAR records |

USD coverage and concentration bounds come from Explorer and NEAR RPC. The separately labeled event inventory comes from BigQuery. Historical private-fill attribution remains unresolved.

## Source map

- [Research pipeline](../src/solverline): collection, receipt classification, Decimal analysis and static evidence build.
- [Thesis](../THESIS.md), [initial spike](SPIKE_RESULT.md), [latest results](RESULTS.md), [sampling scope](../sampling.json).

Own project code: [MIT](../LICENSE). Dependencies retain their respective licenses.

## Archived additional collection

An extra Explorer snapshot was collected during research. Further execution resolution was deferred at the user's request; it is excluded from the completed 555-swap analysis. The [archival scope](data/expanded-cohort.json) and [CSV](data/expanded-swaps.csv) are retained for provenance, with no expanded attribution or warehouse execution claimed.

## Post-hoc sensitivity checks

The dashboard and [short investment brief](INVESTMENT_BRIEF.md) are generated from `solverline.sensitivity`. We remove the largest 1/5/10 swaps across all valid-USD swaps and separately across attributable swaps, then leave out each date. Every case recomputes coverage and account bounds with remaining unknown USD. `data/sensitivity.json` records removed swap IDs. Account recurrence counts distinct sampled dates/windows, not continuous service or independent operators. The offline reproduction checks these products as well as the unchanged baseline summary.

## Durability scenarios and economic units

The observed tiles are distinct from the scenario tiles. Each has a caption and evidence drawer. The model's observed account weights and slice ranges are built into `data/durability-inputs.json`; `data/economic-baseline.json` pins external published annualized gross fees and captured revenue to a source commit and file SHA-256. Sample-scope USD and annualized USD/year are different units and are never added together.

The three controls set assumed attributable share, departure count among observed account IDs, and volume change before departures. No departure or stress event is verified. The calculation assumes no replacement, constant fee yield and transport of the sample account mix to revenue-bearing activity. Moving attribution retains account weights. See the on-page equations and the [walkthrough](DEMO_SCRIPT.md). `node tools/check-durability.cjs` checks the arithmetic and pathological inputs; browser checks exercise keyboard controls and file loading.
