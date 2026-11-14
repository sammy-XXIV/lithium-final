"""Credential-free baseline reproduction: python tools/reproduce.py [--output PATH]."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from solverline.resolve_fillers import resolve, ARCHIVAL_RPC
from solverline.analyze import analyze
from solverline.build_dashboard import build_dashboard


def reproduce(output):
    output = Path(output).resolve()
    if output == ROOT or ROOT == output.parent or output.is_relative_to(ROOT / 'docs') or output.is_relative_to(ROOT / 'src'):
        raise ValueError('Choose a separate output directory, such as reproduced/docs')
    manifest = json.loads((ROOT / 'snapshots/manifest.json').read_text())
    archive = ROOT / 'snapshots/baseline.zip'
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest['archive_sha256']:
        raise ValueError('Snapshot archive checksum mismatch')
    with tempfile.TemporaryDirectory() as temporary:
        cache = Path(temporary)
        with zipfile.ZipFile(archive) as bundle:
            if len(bundle.namelist()) != len(set(bundle.namelist())) or set(bundle.namelist()) != set(manifest['files']):
                raise ValueError('Snapshot member inventory mismatch')
            for name in bundle.namelist():
                target = (cache / name).resolve()
                if not target.is_relative_to(cache.resolve()):
                    raise ValueError('Unsafe snapshot member')
                data = bundle.read(name)
                if hashlib.sha256(data).hexdigest() != manifest['files'][name]:
                    raise ValueError('Snapshot member checksum mismatch')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        # No local .env/cache dependency, no socket connections and no RPC fetch.
        with patch('socket.socket.connect', side_effect=AssertionError('Reproduction attempted network access')):
            rows, provenance = resolve(cache / 'sampling.json', fetch=False, endpoint=ARCHIVAL_RPC,
                                       explorer_directory=cache / 'explorer', rpc_directory=cache / 'rpc',
                                       derived_directory=cache / 'derived')
            if not provenance['receipt_run_complete'] or len(rows) != manifest['swaps'] or provenance['tx_total'] != manifest['transactions']:
                raise ValueError('Incomplete snapshot')
            report = analyze(rows, provenance, directory=cache / 'derived')
            expected = json.loads((ROOT / 'docs/data/summary.json').read_text())
            if report['summary'] != expected:
                raise ValueError('Recomputed summary differs from the published baseline')
            for name in ('sensitivity.json', 'sensitivity.csv', 'account-persistence.csv'):
                if (cache / 'derived' / name).read_text(encoding='utf-8') != (ROOT / 'docs/data' / name).read_text(encoding='utf-8'):
                    raise ValueError(f'Recomputed sensitivity differs: {name}')
            build_dashboard(report, derived=cache / 'derived', docs=output)
            for name in ('durability-inputs.json', 'economic-baseline.json', 'headline.txt', 'stress-evaluation.json'):
                if (output / 'data' / name).read_text(encoding='utf-8') != (ROOT / 'docs/data' / name).read_text(encoding='utf-8'):
                    raise ValueError(f'Recomputed presentation input differs: {name}')
        for name in ('SPIKE_RESULT.md', 'ATTRIBUTION_AUDIT.md'):
            shutil.copyfile(ROOT / 'docs' / name, output / name)
    print(f'Verified all published summary fields: {len(rows)} swaps / {provenance["tx_total"]} graphs. No credentials or network used.')
    print(f'Open {output / "index.html"}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'reproduced/docs')
    args = parser.parse_args()
    reproduce(args.output)
