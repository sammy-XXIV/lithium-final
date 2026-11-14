# Implementation status

- The Explorer collector fetched 555 successful swaps from 24 fixed windows.
- Additional collection and export work was deferred at the user's request. The validated 555-swap study is the published evidence. Extra Explorer snapshots and verified cache files are retained as archival research, excluded from attribution figures. No further collection or export is active or required for the current release.
- All 1,333 linked NEAR transaction response graphs are cached and complete.
- Classifier version 2 attributes 235 swaps / $237,244.08 / 28.37% of sampled USD to 15 executing account IDs. It classifies 361 public swaps (235 attributed, 126 ambiguous), 93 confidential-treasury paths and 101 unresolved. Operator independence remains unverified. The prior zero result is superseded by the documented schema/fee-netting correction.
- The dashboard shows model-free concentration bounds and a conditional one-swap/one-filler sensitivity case. That scenario is not a verified settlement structure.
- The due-diligence panel states the observed diversification verdict, missing evidence and a separate interactive disclosure scenario. Hypothetical percentages assume disjoint contributions from independent operators; invalid totals are rejected and observed figures remain unchanged. No user adoption or actual settlement disclosures are claimed.
- A credential-free snapshot ships all 555 swaps and 1,333 chain result graphs. `python tools/reproduce.py` checks hashes, rebuilds without networking and compares every published summary field; research regression checks cover the release.
- BigQuery event inventory executed across all 24 windows: 263 grouped rows, 9,280 SUCCESS_VALUE logs, 359 FAILURE logs, 11 SUCCESS_RECEIPT_ID logs. The dashboard includes a date chart, per-window CSV, exact SQL and job metadata (identity fields removed). This is not a swap-level reconciliation or recovery of private filler identities.

The [latest results](RESULTS.md), [dashboard](index.html), [thesis](../THESIS.md) describe the current evidence and its limits.

- Post-hoc trade/date exclusions and account recurrence are generated with the baseline, linked to a short investment brief, and checked by offline reproduction. They do not infer operator independence or causal lost volume.

- The static durability model has three assumption sliders and separate sample-volume, annualized gross-fee and captured-revenue outputs. Published external economics are pinned and cited; no replacement, constant fee yield and transport of sample account weights are explicit unverified assumptions.

- Stress-event assessment: not established; no volatile-week or independently documented exit analysis is claimed.
- The interface is a static tile layout with captions, source/query/sample evidence panels, offline controls, local fonts and no runtime package or API-key interface.
- Prior interface work is credited to Vox; external economics and related NEAR research are credited separately. The demo script follows the current static model.
