# Lithium finishing audit — 2026-11-14

Baseline: `e4eeb9dbb0b3255bb287a8b633f6ae11863cde58`, inspected locally and in the public `sammy-XXIV/lithium-final` repository. The older `sammy-XXIV/lithium` URL returned 404.

## Stage 0 — audit

- No auction/FHEVM code, navigation, dependencies, workflow, images or prose found in the tracked release. Substrings in transaction hashes are not references to those technologies.
- `make reproduce` is absent. The shipped instructions instead specify `python tools/reproduce.py`; that command passed in a clean local clone with no raw cache, credentials or installation. It checked all summary fields for 555 swaps and 1,333 transaction graphs. Reproduction extracts the bundled snapshot; it does not collect new data.
- README/THESIS metrics corresponding to `docs/data/summary.json` agree at their displayed precision. Counts, sensitivity results, warehouse event counts and external economics have separate denominators/sources; they are not all fields of summary.json.
- The proposed zero-attribution headline is obsolete. Current evidence reports 235 attributable swaps, $237,244.082545028184, and 15 account IDs. This does not authenticate independent operators. The prior correction is documented in `docs/ATTRIBUTION_AUDIT.md`.
- Baseline gates: offline build and clean-clone reproduction passed; 28 Python tests passed; disclosure and durability JavaScript checks passed. Public Pages workflow 43607241385 succeeded for the baseline commit. No new deployment was requested or triggered.
- Two research-guide image links point to unshipped files. Remove those obsolete links while preparing the documentation; do not invent replacement screenshots.

## Execution plan and gates

Follow the user's stages in order in the existing project, on branch `finish-lithium`. Do not collect, push, publish or submit. Keep the classification rule and sample fixed. After each stage run offline regeneration, the Python suite, both JavaScript scenario checks and the local Pages/browser checks. A new hosted Pages result cannot exist without publishing; use the same build locally and report that distinction.

1. Confirm auction removal is already satisfied; retain the verified research app.
2. Add `make reproduce` and a standard-library command rebuilding analytical tables/charts from shipped `docs/data`, comparing all generated files and summary fields. Retain the separate raw-snapshot attribution replay. Exercise both in clean-checkout CI without publishing.
3. Rewrite the README opening around supported attribution, unverified diversification, investor action, calculator and immediate reproduction actions.
4. Map requested evidence, responsible sources and calculator controls in an analyst checklist.
5. State exact existing reassessment gates and distinguish reassessment from a positive diversification verdict.
6. Credit Andrea Soldano's valuation argument at a pinned file/commit; verify cited figures there and distinguish external published inputs. Consolidate detailed qualifications in each document's Limitations section while keeping essential qualifications beside claims.
7. Inspect unsupported schemas in the existing snapshot. Add support only with proof of semantics and regressions; otherwise retain the rule and report the result. Recompute from the same evidence.

For rollback, preserve a local checkpoint of the stage's starting files; restore only this stage's changes if its gates fail. No unrelated user work was present at the start.

## Stage 1 — already satisfied

No removal was necessary in this release. The baseline gates apply to the identical code and data. Remaining: stages 2–7; no zero-attribution claim will replace the corrected findings.

## Stage 2 — analytical reproduction

Added `make reproduce` / `python tools/reproduce_tables.py`, using only shipped public data for the analytical build. It reconstructs all analysis products through the existing arithmetic and renderer, checks every summary field, and compares all regenerated files. Deliberate summary/table corruption tests fail as expected. Shared embedded JSON serialization is now deterministic; no values or classification rules changed. Removed two unshipped research-guide screenshot links.

Gates: data-only regeneration PASS; raw-snapshot replay PASS; 31 Python tests PASS; both JavaScript scenario checks PASS; browser checks PASS over HTTP and file URLs at desktop/mobile sizes; `git diff --check` PASS. CI now runs the data-only command from a clean Actions checkout, the receipt replay, tests and browser check before assembling Pages. PRs verify without deploying. The changed workflow has not been run on GitHub because nothing has been pushed. Windows has no make installed here; the identical Python target was executed locally.

The data-only command was also run successfully from a new clean local clone after the stage 2 commit, with a clean working tree afterward.

## Stage 3 — README opening

The opening now leads with unverified solver diversification, the supported 235-of-555 account attribution, the investment consequence, calculator links and a Do X / see Y table. No observed operator count is asserted. Gates: analytical build PASS; 31 Python tests PASS (including snapshot replay); both JavaScript scenario checks and Pages browser checks PASS; diff whitespace check PASS. Remaining: stages 4–7.

## Stage 4 — analyst evidence requests

README and THESIS now connect settlement, ownership/aliases, coverage, economics and continuity requests to responsible sources and the actual calculator assumptions. Fixed economic inputs require a sourced rebuild; account departure controls are not an operator-mapping feature, and there is no replacement-rate control. Gates: analytical build PASS; 31 Python tests PASS; both JavaScript scenario checks and Pages browser checks PASS; diff check PASS. Remaining: stages 5–7.

## Stage 5 — breaking points

Added explicit evidence-condition/verdict consequences, using the existing coverage and width gates rather than new fitted thresholds. Complete authenticated coverage/mapping permits measuring sample operator concentration, not assuming diversification. Verified aliases change the identity interpretation; complete replacement at unchanged captured-fee yield contradicts the event's no-replacement loss scenario. Gates: analytical build PASS; 31 Python tests PASS; both JavaScript scenario checks and Pages browser checks PASS; diff check PASS. Remaining: stages 6–7.

## Stage 6 — credit and consolidated qualifications

Added original credited paragraphs linking Andrea Soldano's pinned `thesis/THESIS.md` valuation argument. Retrieved the actual pinned file and verified SHA-256 `d08a0c25e86ed9eb387ebfaad1e876e560c7be8e4707d3b1b84c7e6539f0bf30`; Q5 contains the cited $70.24M gross-fee and $19.19M captured-revenue annualized inputs. No new valuation numbers, external code, prose or document structure were incorporated. Citation verification is explicitly distinguished from independent economic reconciliation.

README and THESIS each have one detailed Limitations section, retaining sampling, method, attribution/identity, bounds, source/economics, warehouse, scenario, stress, adoption and reproduction qualifications. Essential distinctions remain beside the claims. Review also corrected the data-only verifier's per-field diagnostic for absent nullable summary keys, after a failing regression demonstrated it; the overall file comparison already rejected the mismatch. No measurement rule changed.

Gates: analytical build PASS; 32 Python tests PASS, including the added nullable-field regression and receipt replay; both JavaScript scenario checks and Pages browser checks PASS; diff check PASS. Remaining: stage 7 only.

## Stage 7 — schema inventory and final replay

Checked the bundled archive SHA-256 and all 1,333 RPC member hashes. Successful `intents.near` DIP4 logs contain supported 0.3.0, separately versioned 0.3.1 `intents_executed`, and 0.4.3 events. There are no observed unsupported version/event combinations or malformed EVENT_JSON logs in that scope. No additional schema support was justified; the classifier and measurement method are unchanged.

Recomputed results remain 235 attributable swaps, 126 ambiguous public executions, 101 without linked settlement and 93 confidential-treasury paths, in the same 555-swap sample. Attribution is $237,244.082545028184 across 15 account IDs; independent operator identities remain unverified. Updated README, THESIS, research guide, attribution audit and implementation status to explain the review and retained gap.

Gates: full raw-snapshot replay PASS; analytical regeneration PASS for every summary field and generated file; 32 Python tests PASS; both JavaScript scenario checks PASS; Pages browser checks PASS; diff check PASS. All requested local stages are complete. No new collection, push, publication or submission occurred. A changed remote CI/Pages run remains unexecuted because publishing was prohibited; local build/browser verification is not described as a new hosted deployment.

Final implementation review was performed inline against the baseline diff. The nullable-field diagnostic was the substantive correction found and regression-tested; no deferred code findings remain. Local commits preserve the stage checkpoints.
