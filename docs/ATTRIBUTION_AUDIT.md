# Classifier correction: from zero to partial public attribution

The original zero-attribution headline overstated the practical limits demonstrated by our implementation. Two tooling restrictions concealed supported public evidence. This correction uses the **same 555 Explorer swaps and same 1,333 cached complete transaction response graphs**; it is not a wider or new sample. Sampling-config and RPC response hashes are unchanged. [Machine-readable comparison](data/attribution-audit.json).

## Defects and fix

1. **Event-version omission.** The parser rejected `intents_executed` version `0.3.1` and marked its entire linked swap unsupported, despite accepting associated `token_diff` version `0.3.0`. A token_diff records signed changes in an account's token balances. The pinned contract source explicitly versions these events differently. Accept 0.3.1 only for `intents_executed`; do not accept arbitrary unknown schemas.
2. **Two-row, two-token, zero-fee restriction.** The old matcher deliberately accepted only exactly two token_diff records, exactly two assets and zero fees. That conservative restriction was too narrow to justify a general zero-attribution headline. Real executions can have multiple records per executing account, intermediary tokens, gas conversion and protocol fees. The correction aggregates all token_diff records by account and verifies the complete fee-adjusted batch. It does not discard inconvenient records or force a match.

## Replay the historical and current rules

From a fresh clone, run:

```sh
python3 tools/check_attribution_audit.py
```

This runs both attribution functions against the **same** hash-checked snapshot, offline. It reproduces **0 attributable swaps before and 235 after, out of 555**, and checks the before/after monetary fields against [attribution-audit.json](data/attribution-audit.json). No input selection, token amounts, sampling windows or denominator changes between the two runs.

The original attribution function and its numeric helper were recovered from preserved Git commit `79b1803346416e4a0b5cbd55eb1776653778b0be` and are frozen in [classifier_v1.py](../tests/fixtures/classifier_v1.py). The shared final-response validation helper is unchanged. [Provenance](../tests/fixtures/attribution-v1-provenance.json) records source/extract checksums and fingerprints of the historical sampling configuration, Explorer windows and original RPC-response hash map; the command checks those fingerprints against the published custody manifest.

The current public repository begins with the corrected release: that historical Git object is not present in its history. The frozen attribution-only extract makes the comparison runnable without that object. Original source history is provenance from the preserved local archive, not an independent third-party attestation. Sanitized snapshot transport metadata is distinguished from the unchanged chain-response bodies; both real fixture transaction bodies are checked against that same snapshot. This comparison verifies the code change's effect on the bundled evidence, not the truth of private settlements or independent operator identities.

## One concrete receipt: exact amounts, including fees

Use the second swap in [public-fee-netted.json.gz](../tests/fixtures/public-fee-netted.json.gz):

- **Swap ID:** `17df36c90276556ee7be7dab` (the deposit-identity hash; checked by the replay tests).
- **Creation time:** `2026-09-24T16:01:27.898Z`.
- **Settlement transaction:** [`Fuq4JhQmzM71kDygLLDSjRNsSxKvqSgr4PRa3Fw3LzUB`](https://nearblocks.io/txns/Fuq4JhQmzM71kDygLLDSjRNsSxKvqSgr4PRa3Fw3LzUB).
- **Execution receipt:** `BWMaTNkiqz2sXKmND9M5WuvUv7GtRDJmE665zbQJqG3z`, executed by `intents.near` with `SuccessValue`; the linked transaction is `FINAL` and successful.
- **Customer intent hash:** `CmpMdwAK5Qiwu59qLD886srQQJTdNBkv1TcZs7hnzGD2`.
- **Customer account:** `eb4666416387fa7f29ecf12c63f4db4460b41ab409313df42b02905cf475b08a`.
- **Other executing account:** `crux-solver.near`; this is an account ID, not an independently verified operator.
- **Token A:** `nep141:tron-d28a265909efecdcee7c5028585214ea0b96f015.omft.near` (origin).
- **Token B:** `nep141:eth-0xdac17f958d2ee523a2206206994597c13d831ec7.omft.near` (destination).

All figures below are **raw integer token units, not USD or decimal token quantities**. Every token_diff record in this receipt is included. The fee is separately credited by the contract, so `customer delta + other account delta + reported fees` must equal zero for each token.

<!-- receipt-example:start -->
| Token | Customer delta | Other executing-account delta | Reported fees | Sum |
| --- | ---: | ---: | ---: | ---: |
| A (origin) | -100000000000 | 99999900000 | 100000 | 0 |
| B (destination) | 99974800050 | -99974900025 | 99975 | 0 |
<!-- receipt-example:end -->

**Why the old rule returned null:** this same receipt contains DIP4 (NEAR Intents' structured event-log format) `intents_executed` at 0.3.1 alongside token_diff at 0.3.0. The old parser rejected the completion-event version. Even if that version were recognized, the two positive fees violate its zero-fee requirement and the raw deltas do not sum to zero before fees.

**Why the corrected rule accepts this account:** the customer token_diff matches the swap's exact intent hash and asset directions; all customer entries lie in one execution receipt; there are exactly two token_diff accounts; every token closes exactly after the reported fees. Both linked transaction graphs must be complete. The first fixture example separately exercises repeated rows and intermediary tokens.

The tests check that this table matches the actual fixture, and that changing one raw token unit or inserting a third token_diff participant restores a null attribution. Exact closure is necessary, not a claim of independently verified ownership, a deployed-binary/source match or protocol-wide diversification.

## Attribution rule, version 2

- Every linked transaction must have a verified final, complete response graph; use successful `intents.near` receipt outcomes only.
- Establish a customer account through an exact swap intent-hash match and a token_diff spending the origin asset and receiving the destination asset.
- All customer token_diff entries across linked transactions must lie in that single execution receipt and have hashes belonging to the swap. A second execution receipt or unrelated customer intent rejects attribution.
- Count **all** token_diff participants. Exactly two distinct accounts may participate; reject any treasury participant. Never discard a third participant to manufacture a pair. Malformed token_diff structures cannot be silently ignored.
- Parse exact integer amounts. Fees must be nonnegative and any positive fee must belong to a negative delta in its own event and not exceed that debit.
- For **every token**, including intermediary tokens, require `customer deltas + counterparty deltas + reported protocol fees = 0`.
- Require net customer origin debit / destination credit and opposite counterparty directions. Return the other executing **account ID**, not an independently identified company or operator. Preserve every token_diff entry supporting the batch.

NEP245 transfer edges alone are not used to infer counterparties. The contract's TransferMatcher constructs edges from net deltas; those edges do not identify signed economic pairings in a multi-account batch. More-than-two-account executions remain public but unattributed.

## Source and real receipts

Corroborating source at commit `fce0936b1699e0591204ce152a78afc1c1338b35`:

- [Versioned event definitions](https://github.com/near/intents/blob/fce0936b1699e0591204ce152a78afc1c1338b35/contracts/defuse/core/src/events/tests/v0_4_1.rs): token_diff 0.3.0 and intents_executed 0.3.1.
- [TokenDiff execution and reported fees](https://github.com/near/intents/blob/fce0936b1699e0591204ce152a78afc1c1338b35/contracts/defuse/core/src/intents/token_diff.rs): applies the raw signed delta, then separately credits collected protocol fees.
- [Net transfer matching](https://github.com/near/intents/blob/fce0936b1699e0591204ce152a78afc1c1338b35/contracts/defuse/core/src/engine/state/deltas.rs): builds transfer edges without signed receiver pairs.

Source is corroboration, not verification of the deployed binary's source version. Each accepted execution must also pass the exact arithmetic rule on its actual successful receipt logs.

The bundled [public-fee-netted.json.gz](../tests/fixtures/public-fee-netted.json.gz) contains two real Explorer swaps and their complete original RPC result graphs, with transport/credential metadata omitted: the first accepted complex execution and the largest accepted swap. These are regression examples selected after the rule audit, not a representative sample. Expected account IDs are recorded for repeatable testing. The full public evidence extract contains receipt and transaction pointers for all accepted swaps.

## Corrected results and limits

- **235 swaps / $237,244.082545028184 / 28.374829%** of sampled input USD are attributable to **15 executing account IDs**.
- **361 public swaps** comprise the 235 attributed and 126 still ambiguous. **93 confidential-treasury swaps** retain null fillers. **101 swaps** remain unresolved without linked settlement evidence.
- Within the attributable subset, the largest account has **64.48%** of attributed USD and the top three have **91.31%**. These are account-level figures in a selected subset, not protocol-wide solver or operator concentration.
- Across the full sampled valid-USD denominator, bounds without assumptions about unknown-volume allocation (model-free bounds) are top-1 **18.30–89.92%**, top-3 **25.91–97.53%**, HHI (Herfindahl–Hirschman Index, a squared-share concentration measure) **0.0370–0.8122**. **71.63% of USD remains unattributed.** These bounds do not resolve operator aliasing.
- Original five-swap spike remains confidential-treasury with null fillers. No relayer, treasury or fee recipient is assigned from its name or transaction-signer role.

The evidence now supports partial public account attribution, so claiming that public data cannot identify any fillers would be wrong. The stronger remaining question is how the unknown share and operator mappings affect a durability assessment. A wider sample or authenticated private settlement records are still needed for broader conclusions.

## Verification

### Final schema review — 2026-11-14

After the finishing stages, the bundled archive and every RPC member hash were checked again. Successful `intents.near` DIP4 logs in the 1,333 bundled graphs use 0.3.0, separately versioned 0.3.1 `intents_executed`, and 0.4.3. All observed version/event combinations are already supported; no malformed `EVENT_JSON` logs were found in that successful-receipt scope. No new schema acceptance rule was added, and the method was not relaxed.

The same 555 swaps still have 235 `unique_fee_balanced_counterparty`, 126 `ambiguous_public_execution`, 101 `no_linked_settlement` and 93 `linked_treasury_shield_and_release` reasons. None has `unsupported_event_schema` as its final reason. The remaining attribution gap cannot be removed by accepting an additional observed event version. Multi-account ambiguity and missing linkage stay unknown. This is an inventory of the bundled scope, not a claim that all possible protocol event schemas are supported.

`python -m unittest discover -s tests -v` includes both real public examples, the original five confidential examples, invalid and unbalanced fees, unrelated intents, third accounts, malformed third-party records, extra customer execution receipts and float rejection. The offline rebuild and browser CSV arithmetic check cover the corrected totals and bounds. Public fixtures contain no RPC endpoint metadata or credentials.
