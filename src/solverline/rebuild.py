"""One-command collection or offline reproduction of Solverline's static dashboard."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

from .pull_explorer import ROOT
from .resolve_fillers import resolve
from .analyze import analyze
from .build_dashboard import build_dashboard


def run(config=ROOT / 'sampling.json', offline=True, allow_partial=False,
        explorer_directory=None, derived_directory=None, docs_directory=None):
    config = Path(config).resolve()
    baseline_explorer = (ROOT / 'data/raw/explorer').resolve()
    expanded = (config.read_bytes() != (ROOT / 'sampling.json').read_bytes()
                or (explorer_directory is not None and Path(explorer_directory).resolve() != baseline_explorer))
    if expanded:
        if not explorer_directory or not derived_directory or not docs_directory:
            raise ValueError('Expanded collection requires isolated Explorer, derived and docs directories')
        if (Path(explorer_directory).resolve() == baseline_explorer
                or Path(derived_directory).resolve() == (ROOT / 'data/derived').resolve()
                or Path(docs_directory).resolve() == (ROOT / 'docs').resolve()):
            raise ValueError('Expanded collection cannot replace baseline cache or output directories')
    if not offline:
        environment = dict(os.environ, PYTHONPATH=str(ROOT / 'src'))
        command = ([sys.executable, '-m', 'solverline.expand_sample', '--config', str(config), '--directory', str(explorer_directory)]
                   if explorer_directory else [sys.executable, '-m', 'solverline.pull_explorer', '--config', str(config)])
        subprocess.run(command,
                       check=True, env=environment, cwd=ROOT)
    rows, manifest = resolve(config, fetch=not offline, explorer_directory=explorer_directory, derived_directory=derived_directory)
    if not manifest['receipt_run_complete'] and not allow_partial:
        raise RuntimeError('Missing receipt cache inputs. Resume collection, or use --allow-partial for an explicitly provisional dashboard.')
    report = analyze(rows, manifest, directory=derived_directory)
    output = build_dashboard(report, derived=derived_directory, docs=docs_directory)
    print(f'Built {output}: {len(rows)} swaps; {manifest["tx_available"]}/{manifest["tx_total"]} transaction results available.')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--offline', action='store_true')
    mode.add_argument('--fetch', action='store_true')
    parser.add_argument('--config', type=Path, default=ROOT / 'sampling.json')
    parser.add_argument('--explorer-directory', type=Path, help='Isolated expanded Explorer cache')
    parser.add_argument('--derived-directory', type=Path, help='Keep expanded analysis separate from the baseline')
    parser.add_argument('--docs-directory', type=Path, help='Separate expanded preview output')
    parser.add_argument('--allow-partial', action='store_true', help='Build an explicitly provisional snapshot from available receipts')
    args = parser.parse_args()
    try:
        run(args.config, offline=not args.fetch, allow_partial=args.allow_partial,
            explorer_directory=args.explorer_directory, derived_directory=args.derived_directory, docs_directory=args.docs_directory)
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        parser.exit(1, f'{exc}\n')


if __name__ == '__main__':
    main()
