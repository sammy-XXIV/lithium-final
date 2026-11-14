# BigQuery evidence

## Archived export preparation: deferred, not required for the release

**Collection and export work is deferred at the user's request. Do not run the helper unless the user explicitly resumes this research.** The current release uses the completed 555-swap study and its executed event inventory.

`03_expanded_execution_export.sql` requests original warehouse transaction/outcome records for the 14,057 linked transaction hashes in the frozen 5,689-swap expanded Explorer cohort. It joins receipt-origin mappings and applies a bounded historical `block_date` range to every data table. No expanded warehouse results or finality claims are made until an authenticated run and graph validation succeed.

From authenticated Cloud Shell, the prepared helper downloads the SQL and its scope hash, dry-runs it, refuses estimates above an explicit **256 GiB cap**, executes within that cap, verifies exported row count against destination-table metadata, saves the actual job response and downloads a ZIP. It does not enable billing or services. Sandbox limits still apply.

```bash
curl -fsSL https://raw.githubusercontent.com/sammy-XXIV/lithium/main/tools/export-expanded-cloudshell.sh -o lithium-export.sh
bash lithium-export.sh
```

The original job response stays local on import; executing-user identity fields must be removed from any public copy. Raw warehouse records must not be relabeled as fetched RPC responses. Missing nodes, transaction origins, conflicting duplicates or graph mismatches remain unresolved. Shared baseline records must be checked against original cached RPC evidence before an expanded attribution claim.

## Executed baseline evidence

The public event inventory is executed and integrated into the dashboard. It measures verifier event activity, not swaps, USD volume or solver concentration.

Dataset: `bigquery-public-data.crypto_near_mainnet_us`, location **us-east1**. Execution project: `shamble-508513` (Sandbox). See [discovery](DISCOVERY.md) for the user-observed live schemas and the corrected partition-marker filter.

| SQL | Evidence | Scope |
| --- | --- | --- |
| [00_partition_inventory.sql](00_partition_inventory.sql) | [Results](results/00_partition_inventory.json), [provenance](results/00_partition_inventory.provenance.json) | Partition existence; not data completeness |
| [01_verifier_event_inventory.sql](01_verifier_event_inventory.sql) | [Results](results/01_verifier_event_inventory.json), [selected job statistics](results/01_verifier_event_inventory.job-summary.json) | One two-minute window; full job response not imported |
| [02_sample_window_event_inventory.sql](02_sample_window_event_inventory.sql) | [Results](results/02_sample_window_event_inventory.json), [job metadata (identity fields removed)](results/02_sample_window_event_inventory.job.json), [file hashes](results/02_sample_window_event_inventory.provenance.json) | All 24 declared observation windows; source of the dashboard chart |

The wide job returned 263 result groups in all 24 windows. Outcome statuses remain separate: 9,280 SUCCESS_VALUE event logs, 359 FAILURE event logs, and 11 SUCCESS_RECEIPT_ID event logs. Distinct receipts are counted within each event/status group; summing those columns across groups double-counts receipts. The SQL inventories all `intents.near` verifier activity in the windows and has not been joined to Explorer swap IDs. Nonempty results do not prove complete indexing.

## Reproduce the warehouse query

Use an authenticated Google Cloud environment with BigQuery access. No credentials are shipped. First dry-run the exact SQL; review the current scan estimate before executing with a suitable explicit cap. The original estimate was 12,748,608,695 bytes; a later run can differ as the warehouse changes.

```bash
bq --project_id=YOUR_PROJECT --location=us-east1 query \
  --use_legacy_sql=false --dry_run < queries/02_sample_window_event_inventory.sql

# After reviewing the estimate: original execution used a 16 GiB cap.
job="lithium_windows_$(date -u +%Y%m%dT%H%M%SZ)"
bq --project_id=YOUR_PROJECT --location=us-east1 --job_id="$job" query \
  --use_legacy_sql=false --maximum_bytes_billed=17179869184 \
  --max_rows=1000 --format=prettyjson \
  < queries/02_sample_window_event_inventory.sql > lithium-windows.json

bq --project_id=YOUR_PROJECT --location=us-east1 show -j \
  --format=prettyjson "$job" > lithium-windows-job.json
```

Retain the original query, results and job metadata together. Every analytical query filters `block_date` to prune daily partitions. The partition inventory is an INFORMATION_SCHEMA metadata query, so it uses partition IDs instead. Timestamp filters select the observation windows but do not reduce the eight-day partition scan to 48 minutes of storage.

## Reproduce the chart offline

`solverline.bigquery` checks imported SQL/result/job hashes before rendering. The dashboard build exports original warehouse evidence under `docs/data/bigquery/`, alongside a derived `windows.csv`. Its date bars sum successful `intents_executed` event logs within the three windows per date. The window CSV keeps all three execution statuses separate. A full research rebuild also requires the gitignored Explorer/RPC raw cache; see the repository README.

Warehouse-to-Explorer reconciliation, private FAR settlement authentication, and operator identity mapping remain unestablished. No RPC-derived figure is labeled as a BigQuery result.
