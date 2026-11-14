"""Collect a separate frozen wider Explorer cohort, preserving the baseline."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from . import pull_explorer as explorer
from .pull_explorer import ROOT, pull_window, _env, _iso
from .resolve_fillers import write_json


def collect(config=ROOT / 'sampling-expanded.json', directory=ROOT / 'data/raw/explorer-expanded', env=None):
    config, directory = Path(config), Path(directory)
    env = _env() if env is None else env
    fingerprint = hashlib.sha256(config.read_bytes()).hexdigest()
    spec = json.loads(config.read_text())
    directory.mkdir(parents=True, exist_ok=True)
    frozen = directory / '_config.sha256'
    if frozen.exists() and frozen.read_text().strip() != fingerprint:
        raise ValueError('Expanded scope differs from existing cache; choose a different directory')
    frozen.write_text(fingerprint)
    base = env.get('EXPLORER_BASE_URL', 'https://explorer.near-intents.org/api/v0')
    original_get = explorer._get
    windows, hashes = [], set()
    with (directory / '_run.lock').open('x'):
        pass
    try:
        for date in spec['dates']:
            for slot in spec['slots_utc']:
                start = dt.datetime.fromisoformat(f'{date}T{slot}:00+00:00')
                end = start + dt.timedelta(minutes=spec['window_minutes'])
                path = directory / f'{start:%Y%m%dT%H%M}.json'
                body = json.loads(path.read_text()) if path.exists() else None
                if body and (body['start'] != _iso(start) or body['end'] != _iso(end)):
                    raise ValueError('Expanded cached window has a different scope')
                if not body or not body.get('complete'):
                    requests = []
                    def capture(base_url, jwt, params, **kwargs):
                        page = original_get(base_url, jwt, params, **kwargs)
                        requests.append(dict(params=params, rows=len(page),
                                             response_sha256=hashlib.sha256(json.dumps(page, sort_keys=True).encode()).hexdigest()))
                        return page
                    explorer._get = capture
                    try:
                        rows, complete = pull_window(base, env['EXPLORER_JWT'], start, end, spec['statuses'], spec['page_size'])
                    finally:
                        explorer._get = original_get
                    rows = [r for r in rows if start <= dt.datetime.fromisoformat(r['createdAt'].replace('Z', '+00:00')) < end]
                    body = dict(start=_iso(start), end=_iso(end), complete=complete,
                                fetched_at=dt.datetime.now(dt.timezone.utc).isoformat(), count=len(rows), swaps=rows,
                                requests=requests)
                    write_json(path, body)
                if body['count'] != len(body['swaps']) or not body['complete']:
                    raise RuntimeError('Expanded pagination is incomplete; not a final cohort')
                windows.append(dict(start=body['start'], end=body['end'], count=body['count']))
                hashes.update(h for row in body['swaps'] for h in row.get('nearTxHashes', []))
                write_json(directory / '_progress.json', dict(windows_complete=len(windows),
                           windows_total=len(spec['dates']) * len(spec['slots_utc']),
                           swaps=sum(w['count'] for w in windows), linked_hashes=len(hashes)))
                print(f'{path.name}: {body["count"]} swaps; {len(windows)} windows complete; {len(hashes)} hashes', flush=True)
        write_json(directory / '_wanted_hashes.json', sorted(hashes))
        return windows
    finally:
        explorer._get = original_get
        (directory / '_run.lock').unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'sampling-expanded.json')
    parser.add_argument('--directory', type=Path, default=ROOT / 'data/raw/explorer-expanded')
    args = parser.parse_args()
    collect(args.config, args.directory)
