# Classifier correction: from zero to partial public attribution

The original zero-attribution headline overstated the practical limits demonstrated by our implementation. Two tooling restrictions concealed supported public evidence. This correction uses the **same 555 Explorer swaps and same 1,333 cached complete transaction response graphs**; it is not a wider or new sample. Sampling-config and RPC response hashes are unchanged. [Machine-readable comparison](data/attribution-audit.json).

## Defects and fix

1. **Event-version omission.** The parser rejected `intents_executed` version `0.3.1` and marked its entire linked swap unsupported, despite accepting associated `token_diff` version `0.3.0`. The pinned contract source explicitly versions these events differently. Accept 0.3.1 only for `intents_executed`; do not accept arbitrary unknown schemas.
2. **One row was mistaken for one account.** The old matcher required exactly two token_diff records, exactly two assets and zero fees. Real executions can have multiple records per executing account, intermediary tokens, gas conversion and protocol fees. Instead, aggregate all token_diff records by account and verify the complete fee-adjusted batch.

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
- Across the full sampled valid-USD denominator, model-free top-1 bounds are **18.30–89.92%**, top-3 **25.91–97.53%**, HHI **0.0370–0.8122**. **71.63% of USD remains unattributed.** These bounds do not resolve operator aliasing.
- Original five-swap spike remains confidential-treasury with null fillers. No relayer, treasury or fee recipient is assigned from its name or transaction-signer role.

The evidence now supports partial public account attribution, so claiming that public data cannot identify any fillers would be wrong. The stronger remaining question is how the unknown share and operator mappings affect a durability assessment. A wider sample or authenticated private settlement records are still needed for broader conclusions.

## Verification

`python -m unittest discover -s tests -v` includes both real public examples, the original five confidential examples, invalid and unbalanced fees, unrelated intents, third accounts, malformed third-party records, extra customer execution receipts and float rejection. The offline rebuild and browser CSV arithmetic check cover the corrected totals and bounds. Public fixtures contain no RPC endpoint metadata or credentials.
