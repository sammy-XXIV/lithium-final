"""Package only the validated baseline; never fetch or include transport credentials."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from solverline.resolve_fillers import load_windows, RPC_DIR, final_result


def main():
    swaps, scope = load_windows()
    published = json.loads((ROOT / 'docs/data/manifest.json').read_text())
    entries = {'sampling.json': (ROOT / 'sampling.json').read_bytes()}
    for window in scope['windows']:
        data = (ROOT / 'data/raw/explorer' / window['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == next(w['sha256'] for w in published['windows'] if w['file'] == window['file'])
        entries['explorer/' + window['file']] = data
    origins = {}
    for tx in sorted({tx for swap in swaps for tx in swap['nearTxHashes']}):
        raw = (RPC_DIR / (tx + '.json')).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == published['rpc_sha256'][tx]
        body = json.loads(raw)
        assert final_result(body, tx)
        endpoint = urlsplit(body['_meta']['endpoint'])
        # Preserve the public chain response exactly as a JSON value. Replace
        # all transport metadata with its credential-free provider origin.
        sanitized = {'jsonrpc': body.get('jsonrpc', '2.0'), 'id': 'snapshot',
                     'result': body['result'],
                     '_meta': {'endpoint': f'{endpoint.scheme}://{endpoint.hostname}'}}
        entries['rpc/' + tx + '.json'] = json.dumps(sanitized, sort_keys=True, separators=(',', ':')).encode()
        origins[tx] = {'original_cache_sha256': published['rpc_sha256'][tx],
                       'result_sha256': hashlib.sha256(json.dumps(body['result'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()}
    directory = ROOT / 'snapshots'
    directory.mkdir(exist_ok=True)
    archive = directory / 'baseline.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (2026, 11, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, data, compresslevel=9)
    manifest = {'scope': '555-swap validated baseline only', 'swaps': len(swaps),
                'transactions': len(origins), 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                'redaction': 'RPC transport metadata replaced by public provider origin; chain result objects unchanged. Explorer windows unchanged.',
                'files': {name: hashlib.sha256(data).hexdigest() for name, data in sorted(entries.items())},
                'rpc_provenance': origins}
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(f'Packaged {len(swaps)} swaps / {len(origins)} transaction graphs; {archive.stat().st_size:,} bytes.')


if __name__ == '__main__':
    main()
