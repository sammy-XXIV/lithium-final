# Latest cached analysis

**Status: complete receipt collection.**

- Successful sampled swaps: 555.
- Valid input USD: 836107.521017888862.
- Linked transaction responses available: 1333/1333.
- Swaps with complete receipt graphs for every linked transaction: 555.
- Supported executing accounts: 15.
- Attributed input USD: 237244.082545028184.
- Confidential-treasury input USD: 55125.517179720979 (6.6%).
- Conditional one-swap/one-filler lower bounds: top-1 25.9%, top-3 50.0%, HHI 0.1156.
- BigQuery: Executed event inventory across 24 windows; no swap-level reconciliation or solver attribution.

## Coverage by sampled date

| Date | Swaps | Valid input USD | Confidential treasury USD | Public USD | Unresolved USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-09-16 | 73 | 72749.528040172309 | 0 | 68918.631960191296 | 3830.896079981013 |
| 2026-09-24 | 77 | 224621.749830907099 | 0 | 218934.432805973913 | 5687.317024933186 |
| 2026-10-02 | 67 | 92271.189703595392 | 0 | 43097.761570055399 | 49173.428133539993 |
| 2026-10-10 | 71 | 70415.241006503623 | 0 | 68251.550043567307 | 2163.690962936316 |
| 2026-10-18 | 53 | 241315.090763505211 | 0 | 20514.616891455211 | 220800.47387205 |
| 2026-10-26 | 54 | 34080.651034335164 | 0 | 21825.824939090693 | 12254.826095244471 |
| 2026-11-03 | 76 | 34929.451692106897 | 11664.754013568902 | 8021.716350614674 | 15242.981327923321 |
| 2026-11-11 | 84 | 65724.618946763167 | 43460.763166152077 | 54.553682 | 22209.30209861109 |

These figures describe 24 fixed windows (48 minutes), not full days or the protocol.
All linked transaction response graphs are complete for this sample; unsupported or ambiguous evidence remains unclassified. This convenience sample cannot establish a protocol-wide confidentiality trend.
Unattributed volume does not prove concentrated or fragile liquidity.

See [summary.json](data/summary.json), [swaps.csv](data/swaps.csv), and [manifest.json](data/manifest.json).
