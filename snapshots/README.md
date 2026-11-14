# Credential-free baseline snapshot

`baseline.zip` contains the original 24 Explorer windows (555 swaps), the sampling configuration and all 1,333 linked NEAR transaction response graphs. It excludes the deferred expanded collection, credentials, wallet keys, local configuration and private transport metadata.

From the repository root, with Python 3.11+:

```sh
python tools/reproduce.py
```

No package installation or API access is required. The script checks the archive SHA-256 and every member, runs classification and analysis without network connections, compares all summary fields with `docs/data/summary.json`, and writes a separate dashboard at `reproduced/docs/index.html`. The published research is not overwritten.

`manifest.json` records archive/member hashes, original RPC cache hashes and canonical JSON hashes of each unchanged chain `result` object. Explorer window bytes are unchanged. RPC `_meta` is replaced with a public provider origin; the JSON-RPC request ID is normalized to `snapshot`. These changes alter RPC file hashes, so rebuilt cache hashes legitimately differ from the original manifest. No chain result, receipt, log, status or amount is changed.

Original cache hashes agree with the published research manifest. These hashes demonstrate consistency with the collected files, not independent certification of an API response or protocol-wide completeness. The separate BigQuery artifacts are already included in the repository; this script checks and uses them locally without rerunning BigQuery.

Maintainers can regenerate this archive from the original baseline cache using `python tools/package_snapshot.py`. That command never fetches data and rejects inputs whose hashes differ from the published manifest.
