# Solverline: attribution coverage and concentration uncertainty

Date: 2026-11-12. Status: written design for review; implementation has not started.

## Purpose and scientific claim

Build reproducible evidence about how much successful 1Click swap volume an outside observer can attribute to executing accounts. Show concentration on the attributable subset and how unknown attribution changes the possible concentration of the full observed sample.

The initial five-swap result is a feasibility finding only. It does not estimate protocol coverage or concentration. Shared treasury use does not imply a single solver. Missing attribution limits an outsider's ability to verify dependence on fillers; it does not establish fragility, centralization, declining competition or a bearish token valuation.

Success means a reader can distinguish settlement visibility, successful attribution, missing receipts, sample scope, and uncertainty in account concentration. The output must remain useful if every observed filler is unknown: coverage is measurable, concentration is unavailable or broadly bounded.

## Approved direction and implementation boundary

The user approved wider sampling, three-way settlement classification, USD coverage, concentration sensitivity, time comparisons, revised thesis language, and an explicitly secondary distribution-channel chart.

This design covers that analysis pipeline and a static evidence dashboard. It excludes trading, wallets, notifications, external account creation, submission, publishing and deployment. The original BigQuery requirement remains a separate deliverable and must be reported as incomplete until schema discovery, dry run and successful execution provide real evidence. Public RPC data cannot be presented as BigQuery results.

Use the existing Python module layout. Prefer Python 3.11 standard library, Decimal for USD arithmetic, JSON for raw caches and CSV/JSON for derived data. Avoid a database, service backend, scheduler or mandatory runtime chart library. A static SVG dashboard plus downloadable CSVs is sufficient. Use a small browser-side check to recompute coverage and concentration from the shipped rows.

## Collection design: predeclare scope before collecting

The first wider run uses eight UTC dates: 2026-09-16, 2026-09-24, 2026-10-02, 2026-10-10, 2026-10-18, 2026-10-26, 2026-11-03 and 2026-11-11. These span eight weeks while rotating weekdays. On each date collect three fixed two-minute windows: [00:00,00:02), [08:00,08:02), [16:00,16:02). This is 24 windows, 48 minutes total, and is not a census of eight weeks.

Each request uses `numberOfTransactions=1000`, `statuses=SUCCESS`, an explicit start/end timestamp and the documented cursor. Exhaust each window rather than treating one page as representative. Start bounds are exclusive in the API: request one millisecond before the desired start and apply the intended half-open interval locally. Record any evidence that timestamp precision differs. Deduplicate by `(depositAddress, depositMemo)`; empty and absent memos normalize to one null value. Reject conflicting duplicates instead of silently choosing a volume.

Keep the main collection unfiltered by pair and USD size. After collection, stratify by date, UTC slot, directed asset pair and **input USD** bins [0,100), [100,1000), [1000,infinity). This avoids excluding swaps on a different output-side condition: the API's `minUsdPrice` and `maxUsdPrice` apply to both input and output. Pair/size-filtered API pulls remain supported for named supplementary drilldowns, but never pooled into the main trend without a separate denominator. Pair strata without observations remain empty, not zero-confidential estimates.

All swaps returned in each complete window are classified; do not select convenient examples or only large swaps. If the run must stop partway, publish the incomplete window and receipt coverage. Do not silently restrict denominators to successfully resolved rows. A configurable cap may stop collection, but any capped page stream is explicitly incomplete and excluded from the main time comparison.

These fixed windows are a designed convenience sample. No population-wide confidential-share estimate, confidence interval or claim of daily representativeness is justified from them. Conclusions concern sampled windows; expanding to full days is a later collection run under the same tools.

## Cache, rate limits and provenance

- Explorer calls are sequential with at least five seconds between starts, including retries. Honor Retry-After for 429; bounded retry for transient errors; fail clearly for rejected authentication. Never log Authorization or `.env` contents.
- Cache raw response bodies atomically, plus request parameters, fetch UTC time, response status, response hash, schema version, pagination cursor and completeness. Credentials are not cache metadata.
- Reuse complete cached windows on resume. Detect repeated cursors, non-advancing pages and malformed records. An empty page is a valid completed window, not an error or a zero-value data fabrication.
- Cache transaction results by hash and endpoint, recording fetch time and successful-final status. Do not permanently treat a transient RPC error as a completed cache hit. Missing/failed receipts remain an explicit resolution error and can be retried on a later pull.
- Use all linked transaction hashes, deduplicated, not only the first. Verify returned hash matches the request and inspect all relevant successful receipt outcomes. Failed receipt logs cannot prove an executed transfer.
- Historical requests use the documented public archival endpoint `https://archival-rpc.mainnet.near.org`; it is severely rate limited. Default to one outstanding RPC request, a five-second minimum request interval, bounded backoff and resumable caching. If access fails, preserve unknown attribution and the error reason. Do not silently replace unavailable history with recent data.
- Save the sampling configuration before any wider pull and include its SHA-256 in the run manifest. Raw caches stay local/gitignored; ship a minimal evidence extract, exact queries and hashes for independent verification.

## Classification and attribution are different fields

Every swap receives `settlement_class` in `{public, confidential_treasury, unresolved}`, an `attribution_status`, a nullable `filler_account`, reason codes, and evidence pointers. A public settlement may still be unattributable. A transaction signer, relayer, bridge manager, fee recipient or account with 'solver' in its name is never enough for attribution.

Rules, in order:

1. **Confidential treasury:** successful verifier receipts show a transfer of this swap's origin asset to the documented treasury and a corresponding release of the destination asset to the independently linked swap account. Establish the account using linked intent hashes, deposit/withdraw evidence or a unique linked transfer path. Merely seeing the treasury elsewhere in a batch is insufficient. Record both supporting receipt IDs and the linked account. Filler remains null because the shared treasury does not identify the executing FAR maker. If only one leg is visible and another receipt is missing, retain unresolved with a partial-treasury-evidence reason.
2. **Public:** a successful `token_diff` from `intents.near` is linked to this swap through an exact intent-hash match or an independently established unique account/asset flow. Record all candidate executed account deltas. Attribute a single account only when the customer leg and a unique complementary executing account can be demonstrated in that execution. Multi-party netting, bundled unrelated swaps, ambiguous paths or multiple candidate fillers keep the filler null and explain the ambiguity. No amount-only coincidence or name-based heuristic.
3. **Unresolved:** insufficient evidence for either class, missing hashes, RPC failures, unknown event schema, incomplete receipt graph or inconsistent linkage. Absence of `token_diff` alone proves neither confidentiality nor public settlement.

If public attribution cannot be implemented confidently for a real observed event shape, leave those swaps unattributed. Tests can establish logic on synthetic cases but cannot validate a real account identity that evidence does not support.

Concentration is measured over observable **executing account IDs**, not proven independent companies or economic solvers. Multiple account IDs may share an operator. That additional entity-resolution uncertainty is stated separately; the bounds below do not solve it.

## Denominators and data quality

Use finite, nonnegative `amountInUsd`, parsed as Decimal, with explicit handling of zero. Missing/invalid USD is never silently coerced to zero. Report count and known value of excluded records, and the number of records whose USD value cannot be established. Coverage for the remaining valid-USD rows is conditional on that denominator.

Each date/slot/pair/size breakdown reports total valid USD and count, confidential-path USD, public-path USD, unresolved-path USD, attributable USD, unattributed USD and receipt-fetch completeness. The three settlement classes sum to the valid-USD denominator. Attributable plus unattributed also sums to it. Do not equate non-confidential with attributable.

For total valid USD T and attributed USD A, publish attributed coverage A/T, confidential-path volume/T, public-path volume/T and unresolved-path volume/T. At T=0 all ratio metrics are null and displayed as unavailable. Keep settlement opacity separate from RPC access failures. A cache outage must not appear as a confidentiality trend.

## Concentration and uncertainty bounds

Let attributed volumes by executing account be a1 >= a2 >= ... >= ak >= 0, A=sum(ai), unknown volume U=T-A. Full-denominator shares use T; attributable-subset concentration uses A. Show which denominator every number uses. HHI uses the [0,1] convention, with any [0,10000] display conversion labeled.

For N in {1,3,10}, let SN be the sum of the largest min(N,k) attributed account volumes. With no limit on the number of additional accounts and unknown volume allowed to accrue to known or new accounts:

- Full-sample top-N lower bound: SN/T.
- Full-sample top-N upper bound: min(1,(SN+U)/T).
- Full-sample HHI lower bound: sum(ai^2)/T^2.
- Full-sample HHI upper bound: ((a1+U)^2 + sum(i>1,ai^2))/T^2; use a1=0 if there are no known accounts.

Lower bounds are conservative **infima under divisible unknown volume and arbitrarily many accounts**, not necessarily attainable assignments of this finite set of swaps. The program must label them as conservative outer bounds, not exact minima over indivisible swaps. Upper bounds allocate all U to the largest known account (or one new account if none is known). Zero known volume yields top-N [0,1] and HHI [0,1] as conservative bounds, while attributable-subset metrics are unavailable. With U=0 the intervals collapse to ordinary observed account concentration.

These are uncertainty intervals over the **observed valid-USD sample**, not confidence intervals and not bounds on eight weeks of protocol volume. Underlying-operator concentration may differ if account IDs are consolidated. Do not attribute confidential volume to a made-up 'unknown solver' and report that as observed concentration.

## Time comparison and secondary dependency

Plot confidential-path share and attributable coverage by sampled date, with the three UTC slots visible in the evidence table. Display denominators and unresolved/RPC-failure share alongside them. Describe directional changes as exploratory window comparisons. Also show within-pair and within-size cells; changing pair/size composition can explain an aggregate change. Small/empty cells stay visible as such. Do not announce a rising trend until the data supports it.

Secondary distribution charts use Explorer `referral` and `appFees.recipient` as explicitly different fields. A missing referral is unknown, not an app. For fee recipients, a swap can name multiple recipients: report overlapping incidence shares that may sum above 100%, or a separately labeled fractional allocation. Never add full swap volume to each recipient and call the resulting total unique volume. These fields identify distribution/fee-routing dependencies, not liquidity providers, solver identities or fee revenue.

## Rebuild, dashboard and evidence

- `python -m solverline.rebuild --offline` regenerates every shipped CSV, summary and chart from complete cached inputs, with no network or credentials required. Missing raw inputs stop with a specific error; no synthetic fallback results.
- `python -m solverline.rebuild --fetch --config sampling.json` fetches/resumes explicit scope, resolves transactions and rebuilds. Package metadata makes the module command work after one documented local install. `make rebuild` delegates to the offline command.
- Published charts: USD coverage over sampled dates; account concentration with outer bounds; pair/size coverage table; clearly secondary referral and fee-recipient charts. If attribution is zero, show the unavailable metric and bounds honestly.
- Each chart has a plain-language sentence, denominator/scope, exact API query or computation, downloadable input CSV and linked receipt/transaction evidence. No fake SQL is attached to an API-only chart.
- Ship a manifest with cache hashes, sample windows, exclusions, partial windows, RPC failures, coverage and calculation version. The browser rechecks USD coverage and bounds from the published aggregate account volumes and unknown volume, without depending on server-side state.
- Update README, THESIS and HANDOFF to the revised question. Preserve evidence for and against the proposed interpretation. Explain that actual all-volume maker concentration is not identifiable for confidential settlement without additional data; this does not prevent analysis of supported public settlement.

## What data would resolve the uncertainty

An authorized export or verifiable disclosure must link each Explorer swap/deposit identity and intent hash to the executed FAR settlement, its account-level signed token deltas, amounts and timestamps. Operator identity mapping is additionally needed for company-level concentration. Document export coverage and possible selective disclosure; receiving some records does not justify imputing the rest. The tool does not attempt to bypass private access or infer secret identities.

## Acceptance and focused verification

1. Fixture-based collector checks exercise pagination beyond 1000, null memos, half-open windows, conflicting duplicates, repeated cursors, retries and resume without refetching complete pages.
2. Classifier checks distinguish the shared treasury, unrelated batched treasury events, failed receipts, relayers, missing receipts, a linked public complementary account and ambiguous multi-account execution. The original five swaps remain unattributed and retain their evidence.
3. Arithmetic checks cover missing USD, zero totals, mixed classification, no known accounts, no unknown volume and all-unknown volume. Every breakdown reconciles exactly in Decimal arithmetic.
4. Bounds are compared with exhaustive finite assignments in small examples: every feasible assignment lies inside the outer bounds; merging unknown volume into the largest account attains the upper HHI; no-unknown intervals collapse. A finite-swap lower bound is never advertised as exact.
5. All fetched windows and RPC coverage are auditable; missing historical responses affect unresolved coverage, not confidential classification. Display and downloads use the same denominators.
6. A verified offline rebuild reproduces output hashes from fixed input/config and never touches the network. Browser checks recompute published figures. No token appears in derived files or docs.
7. If BigQuery credentials remain absent, the dashboard and README explicitly state that the original BigQuery deliverable is incomplete. Schema-dependent SQL cannot be claimed executed or populated using RPC results.

## Source references checked during design

- [Explorer OpenAPI](https://explorer.near-intents.org/api/v0/openapi.yaml): size, date, token and pagination semantics; local copy `data/raw/spike/openapi.yaml`.
- [Confidential settlement](https://docs.near-intents.org/integration/market-makers/confidential-intents): shared treasury and private FAR execution.
- [NEAR RPC providers](https://docs.near.org/api/rpc/providers): archival endpoint and severe public rate limits.
- [NEAR BigQuery](https://docs.near.org/data-infrastructure/big-query): source/table discovery and partition-filter guidance; live dataset coverage still needs verification.
