# Solver attribution spike — 2026-11-12

**Verdict: NOT IDENTIFIABLE for the five sampled swaps from public receipts.**

Explorer authentication succeeded. We fetched the five latest `SUCCESS` records at pull time and inspected all 19 linked NEAR transactions, rather than assuming the first hash was settlement. Every transaction returned a successful final result. All five swaps show transfers into and out of the same confidential treasury. None of their linked public receipts contains a `token_diff` event.

This does **not** mean that one solver fills all volume. It means the sampled public paths do not reveal their executing market makers. It also does not prove every Explorer swap is confidential.

## Scope and query

`GET https://explorer.near-intents.org/api/v0/transactions?numberOfTransactions=5&statuses=SUCCESS`

- Swap creation times: 2026-11-12 18:14:56.739–18:15:37.049 UTC.
- Sampling: latest completed records returned by the API, a convenience sample covering approximately 40 seconds of creation times. Not random; not representative of a day or the protocol.
- Input volume field: `amountInUsd`, summed exactly as decimal strings: **$5,153.553941205949**. This is the sample total, not protocol volume.
- RPC: `EXPERIMENTAL_tx_status`, parameters `[transaction_hash, "intents.near"]`, at `https://rpc.mainnet.near.org`.
- No BigQuery queries or paid services were used.

## Evidence by swap

The hash below identifies a linked transaction with a transfer of the origin asset into the treasury. Every linked transaction, account list and structured event is included in [spike-evidence.json](spike-evidence.json).

| Sample | Created at (UTC) | Input USD | Linked txs | Treasury transfer transaction |
| --- | --- | ---: | ---: | --- |
| 1 | 18:15:37.049 | 27.607776234478 | 4 | [6fUB2oWHMbQCx1hQdmf7iGxBKALPzcc7VBcHBj1vLANE](https://nearblocks.io/txns/6fUB2oWHMbQCx1hQdmf7iGxBKALPzcc7VBcHBj1vLANE) |
| 2 | 18:15:17.567 | 77.509782158587 | 4 | [ETFxiwtLJLjvDtd6GmucEyMLFBQrAeCmSqWjB8n1LhNi](https://nearblocks.io/txns/ETFxiwtLJLjvDtd6GmucEyMLFBQrAeCmSqWjB8n1LhNi) |
| 3 | 18:15:02.117 | 39.989302812884 | 4 | [7csA5sUoSx1VS2EPjWTY36Pgry5xT2FrQtgZBgaRgN2e](https://nearblocks.io/txns/7csA5sUoSx1VS2EPjWTY36Pgry5xT2FrQtgZBgaRgN2e) |
| 4 | 18:14:58.338 | 4996.350000000000 | 3 | [8GmcM3JEGmxWKTZgQDevfWhx29sWKPhN8oyE32soHuHp](https://nearblocks.io/txns/8GmcM3JEGmxWKTZgQDevfWhx29sWKPhN8oyE32soHuHp) |
| 5 | 18:14:56.739 | 12.097080000000 | 4 | [mVAa2uUQgBcWfLR6BKFLCf4Kwc7buUZ4cfDZkxsw3Qk](https://nearblocks.io/txns/mVAa2uUQgBcWfLR6BKFLCf4Kwc7buUZ4cfDZkxsw3Qk) |

## Why the repeated account is not a solver

The visible account is:

`51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe`

Official [Confidential Intents documentation](https://docs.near-intents.org/integration/market-makers/confidential-intents) identifies this as the common treasury used for shielding and unshielding. It describes settlement on FAR through `intents.far`, with private RPC access and swap execution hidden from public indexers. The [configuration example](https://docs.near-intents.org/integration/market-makers/confidential-example) names this exact account as `PRIVATE_TREASURY_ACCOUNT_ID`, shared across solver operators.

The observed transfer pattern is consistent with that documented architecture. We therefore classify these as confidential treasury paths and leave their filler field null. A public transaction's `signer_id` of `intents.near`, or the inbound bridge signer `bridge-mng.near`, is not proof of which market maker filled it.

Sample 3's unshield transaction also releases assets to `solver-multichain-asset.near` and another implicit account. These are observable recipients in a bundled release; their presence does not establish a unique executing counterparty for this swap. We do not assign a solver from the account name or co-occurrence.

## Reproduction and checks

- Original Explorer response: `data/raw/spike/swaps.json`.
- Original RPC responses: `data/raw/spike/tx-<hash>.json` (19 files).
- Public structured extract: [spike-evidence.json](spike-evidence.json), including SHA-256 hashes of all original JSON files.
- Contract source examined: [near/intents at fce0936](https://github.com/near/intents/tree/fce0936b1699e0591204ce152a78afc1c1338b35), which defines the `dip4` event types. This checkout is corroborating source, not proof of the deployed binary's version.
- Local throwaway collection script: `python data/raw/spike/probe.py`. It reads `.env`, reuses cached responses and fetches missing ones. It is not the production pipeline.
- Local offline extraction/check: `python data/raw/spike/summarize.py`. It verifies successful status and hash identity for all 19 transactions, finds both treasury legs for each swap, and regenerates the public extract. These scripts and raw responses are local, gitignored research artifacts.

To check the shipped extract alone, from the project directory:

```python
import json
from decimal import Decimal
from pathlib import Path

e = json.loads(Path('docs/spike-evidence.json').read_text())
assert len(e['samples']) == 5
assert sum(len(s['transactions']) for s in e['samples']) == 19
assert all(s['filler'] is None for s in e['samples'])
assert not any(x['event']['event'] == 'token_diff'
               for s in e['samples'] for t in s['transactions'] for x in t['events'])
print(sum(Decimal(s['amount_in_usd']) for s in e['samples']))
```

## Consequence for the thesis

Do not compute top-N solver shares or HHI by assigning the treasury to a single solver. Do not turn missing attribution into evidence of concentrated liquidity. Public BigQuery receipt logs would expose the public side of these paths; a different indexer does not by itself reveal private FAR settlement.

Recommended next research question: **What share of 1Click volume can an independent observer attribute to executing accounts, and how sensitive are concentration estimates to the unknown share?** Expand the sample across dates and pairs, classify public vs confidential paths, and report unresolved coverage explicitly. Actual all-volume solver concentration would require additional authorized data that exposes private settlement and its mapping to the Explorer records.

The handoff's alternate distribution-channel analysis remains possible, but measures a different dependency. No fallback pipeline has been built and no concentration or token-value claim is established.
