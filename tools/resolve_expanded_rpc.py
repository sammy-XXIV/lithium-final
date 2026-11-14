"""Bounded sequential RPC fallback for the expanded cohort; leaves baseline live."""
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from solverline.resolve_fillers import load_windows, RpcCache, configured_rpc, RPC_DIR, write_json


if __name__ == '__main__':
    rows, manifest = load_windows(ROOT / 'sampling-expanded.json', ROOT / 'data/raw/explorer-expanded')
    hashes = sorted({h for row in rows for h in row.get('nearTxHashes', [])})
    lock = RPC_DIR / '_run.lock'
    with lock.open('x') as handle:
        handle.write(str(os.getpid()))
    cache = RpcCache(endpoint=configured_rpc())
    progress = ROOT / 'data/derived/expanded-rpc-progress.json'
    stop = ROOT / 'data/raw/explorer-expanded/_stop_rpc'
    started = time.time()
    try:
        available = sum(cache.read(h) is not None for h in hashes)
        checked = 0
        for index, txhash in enumerate(hashes, 1):
            if stop.exists():
                write_json(progress, dict(status='stopped', checked=checked, available=available, total=len(hashes)))
                break
            was_cached = cache.read(txhash) is not None
            result = cache.fetch(txhash)
            if result and not was_cached:
                available += 1
            checked = index
            if index % 10 == 0 or not was_cached or index == len(hashes):
                write_json(progress, dict(status='collecting', pid=os.getpid(), checked=index, available=available,
                           total=len(hashes), started_unix=started, updated_unix=time.time(), errors=len(cache.errors)))
            if index % 50 == 0:
                print(f'Expanded RPC {index}/{len(hashes)} checked; {available} complete; {len(cache.errors)} errors', flush=True)
            if cache.provider_refused:
                write_json(progress, dict(status='provider_refused', available=available, total=len(hashes)))
                break
        else:
            write_json(progress, dict(status='complete' if available == len(hashes) else 'partial',
                       available=available, total=len(hashes), errors=len(cache.errors)))
            print('Expanded receipt collection finished; expanded analysis still requires an explicit validated build.', flush=True)
    finally:
        lock.unlink(missing_ok=True)
