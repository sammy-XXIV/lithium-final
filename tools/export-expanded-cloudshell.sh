#!/usr/bin/env bash
# Run in the user's authenticated Cloud Shell. Never enables billing or services.
set -euo pipefail
revision="${1:-main}"
project="shamble-508513"
maximum=274877906944 # Explicit 256 GiB maximum scan; sandbox limits still apply.
root="https://raw.githubusercontent.com/sammy-XXIV/lithium/${revision}"
curl -fsSL "$root/queries/03_expanded_execution_export.sql" -o lithium-expanded.sql
curl -fsSL "$root/docs/data/expanded-cohort.json" -o lithium-expanded-cohort.json
python3 - <<'PY'
import hashlib,json
from pathlib import Path
scope=json.loads(Path('lithium-expanded-cohort.json').read_text())
if scope.get('status') != 'explorer_complete_execution_resolution_pending':
    raise SystemExit('This export is deferred. No warehouse query will run.')
assert hashlib.sha256(Path('lithium-expanded.sql').read_bytes()).hexdigest()==scope['prepared_sql_sha256']
print('Frozen Explorer scope:',scope['count'],'swaps;',scope['linked_hashes'],'requested transaction hashes')
PY
bq --project_id="$project" --location=us-east1 query --use_legacy_sql=false \
  --dry_run < lithium-expanded.sql > lithium-expanded-dry-run.txt 2>&1
cat lithium-expanded-dry-run.txt
estimated="$(python3 - <<'PY'
import re
from pathlib import Path
match=re.search(r'process ([0-9]+) bytes',Path('lithium-expanded-dry-run.txt').read_text())
if not match: raise SystemExit('Cannot read dry-run estimate; no query executed.')
print(match.group(1))
PY
)"
if [[ "$estimated" -gt "$maximum" ]]; then
  echo "Estimate exceeds the 256 GiB cap. No query executed."
  exit 1
fi
job="lithium_expanded_$(date -u +%Y%m%dT%H%M%SZ)"
bq --project_id="$project" --location=us-east1 --job_id="$job" query \
  --use_legacy_sql=false --maximum_bytes_billed="$maximum" \
  --max_rows=1000000 --format=prettyjson < lithium-expanded.sql > lithium-expanded-records.json
bq --project_id="$project" --location=us-east1 show -j --format=prettyjson "$job" > lithium-expanded-job.json
destination="$(python3 - <<'PY'
import json
from pathlib import Path
d=json.loads(Path('lithium-expanded-job.json').read_text())
assert d['status']['state']=='DONE' and 'errorResult' not in d['status']
t=d['configuration']['query']['destinationTable']
print(t['projectId']+':'+t['datasetId']+'.'+t['tableId'])
PY
)"
bq --project_id="$project" --location=us-east1 show --format=prettyjson "$destination" > lithium-expanded-table.json
python3 - <<'PY'
import json
from pathlib import Path
rows=json.loads(Path('lithium-expanded-records.json').read_text())
table=json.loads(Path('lithium-expanded-table.json').read_text())
assert len(rows)==int(table['numRows']), 'Results truncated: do not use this export.'
job=json.loads(Path('lithium-expanded-job.json').read_text())
q=job['statistics']['query']
print('Complete export:',len(rows),'warehouse records; job',job['jobReference']['jobId'])
print('Processed bytes:',q['totalBytesProcessed'],'billed bytes:',q['totalBytesBilled'])
PY
python3 -m zipfile -c lithium-expanded-evidence.zip lithium-expanded.sql \
  lithium-expanded-cohort.json lithium-expanded-records.json lithium-expanded-job.json \
  lithium-expanded-table.json lithium-expanded-dry-run.txt
cloudshell download lithium-expanded-evidence.zip
