"""Offline before/after attribution replay and exact worked-receipt arithmetic."""
from collections import defaultdict
import gzip
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from solverline.analyze import aggregate
from solverline.resolve_fillers import classify_swap, final_result, load_windows


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def historical_classifier():
    provenance = read_json(ROOT / 'tests/fixtures/attribution-v1-provenance.json')
    source = ROOT / 'tests/fixtures/classifier_v1.py'
    if hashlib.sha256(source.read_bytes()).hexdigest() != provenance['extract_sha256']:
        raise ValueError('Historical classifier extract checksum mismatch')
    helper = inspect.getsource(final_result).replace('\r\n', '\n').rstrip('\n')
    if hashlib.sha256(helper.encode()).hexdigest() != provenance['shared_final_result_source_sha256']:
        raise ValueError('Shared response-validation helper differs from historical source')
    spec = importlib.util.spec_from_file_location('historical_classifier_v1', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, provenance


def example_table():
    fixture = json.loads(gzip.decompress((ROOT / 'tests/fixtures/public-fee-netted.json.gz').read_bytes()))
    swap = fixture['swaps'][1]
    result = classify_swap(swap, fixture['transactions'])
    customer = 'eb4666416387fa7f29ecf12c63f4db4460b41ab409313df42b02905cf475b08a'
    maker = 'crux-solver.near'
    if result['filler_account'] != maker:
        raise ValueError('Worked receipt no longer attributes the documented executing account')
    totals, fees = defaultdict(lambda: defaultdict(int)), defaultdict(int)
    for event in result['evidence']:
        data = event['data']
        for token, amount in data['diff'].items():
            totals[data['account_id']][token] += int(amount)
        for token, amount in data.get('fees_collected', {}).items():
            fees[token] += int(amount)
    lines = ['| Token | Customer delta | Other executing-account delta | Reported fees | Sum |',
             '| --- | ---: | ---: | ---: | ---: |']
    for label, token in [('A (origin)', swap['originAsset']), ('B (destination)', swap['destinationAsset'])]:
        c, m, fee = totals[customer][token], totals[maker][token], fees[token]
        if c + m + fee != 0:
            raise ValueError('Worked receipt is not exactly closed')
        lines.append(f'| {label} | {c} | {m} | {fee} | {c + m + fee} |')
    return '\n'.join(lines)


def verify():
    legacy, provenance = historical_classifier()
    published = read_json(ROOT / 'docs/data/manifest.json')
    for expected, actual in [('config_sha256', published['config_sha256']),
                             ('rpc_sha256_map_sha256', digest(published['rpc_sha256'])),
                             ('explorer_windows_sha256', digest(published['windows']))]:
        if provenance[expected] != actual:
            raise ValueError('Historical evidence custody mismatch: ' + expected)
    manifest = read_json(ROOT / 'snapshots/manifest.json')
    archive = ROOT / 'snapshots/baseline.zip'
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest['archive_sha256']:
        raise ValueError('Snapshot archive checksum mismatch')
    with tempfile.TemporaryDirectory() as temporary, zipfile.ZipFile(archive) as bundle:
        cache, transactions = Path(temporary), {}
        if len(bundle.namelist()) != len(set(bundle.namelist())) or set(bundle.namelist()) != set(manifest['files']):
            raise ValueError('Snapshot inventory mismatch')
        for name in bundle.namelist():
            body = bundle.read(name)
            if hashlib.sha256(body).hexdigest() != manifest['files'][name]:
                raise ValueError('Snapshot member checksum mismatch: ' + name)
            if name.startswith('rpc/'):
                transactions[Path(name).stem] = json.loads(body)
            else:
                target = (cache / name).resolve()
                if not target.is_relative_to(cache):
                    raise ValueError('Unsafe snapshot member')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('Audit attempted network')):
            rows, custody = load_windows(cache / 'sampling.json', cache / 'explorer')
            if custody['config_sha256'] != provenance['config_sha256'] or digest(custody['windows']) != provenance['explorer_windows_sha256']:
                raise ValueError('Bundled Explorer evidence differs from historical custody')
            before = [{**swap, **legacy.classify_swap(swap, transactions)} for swap in rows]
            after = [{**swap, **classify_swap(swap, transactions)} for swap in rows]
        audit = read_json(ROOT / 'docs/data/attribution-audit.json')
        for name, classified in [('before', before), ('after', after)]:
            actual = aggregate(classified)
            for key, expected in audit[name].items():
                if actual[key] != expected:
                    raise ValueError(f'{name} audit mismatch: {key}')
        fixture = json.loads(gzip.decompress((ROOT / 'tests/fixtures/public-fee-netted.json.gz').read_bytes()))
        for tx_hash, response in fixture['transactions'].items():
            if response['result'] != transactions[tx_hash]['result']:
                raise ValueError('Worked fixture transaction body differs from snapshot')
        if len(rows) != manifest['swaps'] or len(transactions) != manifest['transactions']:
            raise ValueError('Snapshot sample count mismatch')
    return {'sample_swaps': len(rows), 'rpc_graphs': len(transactions),
            'before_swaps': sum(row['attribution_status'] == 'attributed' for row in before),
            'after_swaps': sum(row['attribution_status'] == 'attributed' for row in after)}


if __name__ == '__main__':
    try:
        result = verify()
        print(f'PASS same evidence: {result["sample_swaps"]} swaps / {result["rpc_graphs"]} graphs; historical {result["before_swaps"]} attributable -> current {result["after_swaps"]}.')
        print('PASS historical custody, extract/helper checksums and worked-fixture transaction bodies.')
        print(example_table())
    except (AssertionError, KeyError, OSError, ValueError) as error:
        print(f'FAIL: {error}')
        sys.exit(1)
