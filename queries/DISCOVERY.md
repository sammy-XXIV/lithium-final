# BigQuery discovery

Status: dataset and schemas confirmed through the user's authenticated Cloud Shell. The corrected partition-metadata query and the first two-minute analytical event inventory have executed. Pasted results and selected actual job statistics are saved under `results/`. The 24-window event inventory and its full job response have now been imported from the downloaded archive. The event inventory is integrated into the dashboard with source downloads. Swap-level reconciliation and private filler identification remain unestablished.

- User project: `shamble-508513` (Sandbox).
- Public dataset: `bigquery-public-data.crypto_near_mainnet_us`.
- Dataset location: **us-east1**, from `bq show`.
- `transactions`, `execution_outcomes`, `receipt_details`, and `receipt_origin_transaction` are daily partitioned on `block_date`, from `bq ls`.
- `transactions` exposes transaction hash, signer, receiver, status, converted receipt ID and UTC block timestamp.
- `execution_outcomes` exposes receipt ID, executor, status and UTC block timestamp. Log strings are stored as `logs.list[].element`: nullable `logs` RECORD, repeated `list` RECORD, nullable STRING `element`. The nested `outcome_receipt_ids` schema has not been inspected.
- `receipt_details` exposes receipt ID, predecessor, receiver, kind and receipt string.
- `receipt_origin_transaction` exposes receipt ID and `originated_from_transaction_hash`.

The first partition metadata query's dry run estimated 10,485,760 bytes. Its initial filter `LENGTH(partition_id) = 8` also admitted the eight-character `__NULL__` marker, so MAX returned that marker for all four tables. The corrected numeric-date filter returned first partition `20200723` and latest partition `20261113` for all four tables. Job ID: `lithium_partitions_20261113T145611Z`, project `shamble-508513`, region `us-east1`. The dry-run estimate was 10,485,760 bytes; actual execution statistics have not yet been imported.

The partition inventory contains metadata observations, not transaction-level results. No data freshness or coverage conclusion follows from table existence or the invalid initial maximum.

## First analytical execution

`01_verifier_event_inventory.sql` ran against `intents.near` execution logs for **2026-11-11 16:00:00 inclusive to 16:02:00 exclusive UTC**. Job `lithium_events_20261113T150935Z` completed with no reported error, cacheHit false, 1,605,049,184 bytes processed and 1,605,369,856 bytes billed across one partition. The 2 GiB cap was respected. Results and selected job statistics were transcribed from the user's Cloud Shell output; this is not a direct API import or a saved full job response.

The nine result groups contain 661 event logs with SUCCESS_VALUE and 16 with FAILURE. There are 167 successful `dip4` / `0.4.3` `intents_executed` logs on 167 distinct receipts within that group, and six successful `token_diff` logs on two receipts. `transfer` has 188 successful logs on 133 receipts and 16 failure logs on 16 receipts. Failure logs must not be treated as completed transfers.

Counts are verifier event logs and group-specific distinct receipts, **not swaps, independently identified solvers, or USD volume**. The same receipt can appear in multiple event groups; summing group receipt counts does not yield a distinct-receipt total. No correspondence to Explorer swaps or classifier failures has yet been established. One two-minute window cannot establish a trend. The event inventory does not change the existing attribution results.

## All 24 observation windows

Imported the original SQL, 263 result rows and full job JSON from the user's downloaded `lithium-bigquery.zip`. Job `lithium_windows_20261113T152520Z` completed without a reported error in `us-east1`, cacheHit false, with 12,748,608,695 bytes processed and 12,749,635,584 bytes billed across eight partitions, below the 16 GiB cap. Archive and imported-file SHA-256 hashes are retained in the provenance JSON.

Results contain event groups for all 24 declared two-minute windows on the eight sampled dates. Event log totals by execution status are 9,280 SUCCESS_VALUE, 359 FAILURE and 11 SUCCESS_RECEIPT_ID. Keep SUCCESS_RECEIPT_ID separate: it can indicate a continuation and does not itself establish completion of downstream execution. These are log counts, not swaps or identified solvers. Presence of results in each window is not proof of full indexing or coverage of Explorer swaps. The event inventory is integrated into the dashboard; USD attribution results remain unchanged.

Published job JSON removes `user_email` and `principal_subject`. The original is retained locally in the ignored raw cache and downloaded archive; provenance records its hash and the sanitized public-file hash. Query configuration, status and execution statistics remain available.
