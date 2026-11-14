"""Background receipt collection followed by a final offline dashboard rebuild."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'src'))
from solverline.resolve_fillers import write_json

state = root / 'data/derived/run-status.json'
lock = root / 'data/raw/rpc/_run.lock'
lock.parent.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, PYTHONPATH=str(root / 'src'), PYTHONUNBUFFERED='1')

if __name__ == '__main__':
    # Exclusive creation prevents accidentally starting two rate-limited collectors.
    with lock.open('x') as handle:
        handle.write(str(os.getpid()))
    try:
        write_json(state, {'status': 'collecting', 'pid': os.getpid(), 'started_unix': time.time()})
        subprocess.run([sys.executable, '-u', '-m', 'solverline.resolve_fillers', '--fetch'],
                       cwd=root, env=env, check=True)
        write_json(state, {'status': 'building', 'pid': os.getpid()})
        subprocess.run([sys.executable, '-m', 'solverline.rebuild', '--offline', '--allow-partial'],
                       cwd=root, env=env, check=True)
        manifest = json.loads((root / 'data/derived/manifest.json').read_text())
        complete = manifest['receipt_run_complete']
        write_json(state, {'status': 'complete' if complete else 'partial',
                          'tx_available': manifest['tx_available'], 'tx_total': manifest['tx_total']})
        print('Final offline rebuild complete.', flush=True)
    except Exception as exc:
        write_json(state, {'status': 'failed', 'error_type': type(exc).__name__})
        raise
    finally:
        lock.unlink(missing_ok=True)
