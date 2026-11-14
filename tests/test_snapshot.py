"""Prove a fresh checkout can reproduce the baseline without private cache or JWT."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SnapshotTests(unittest.TestCase):
    def test_fresh_checkout_reproduces_without_private_cache(self):
        spec = importlib.util.spec_from_file_location('reproduce_baseline', ROOT / 'tools/reproduce.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / 'checkout'
            shutil.copytree(ROOT / 'snapshots', checkout / 'snapshots')
            shutil.copytree(ROOT / 'docs/data', checkout / 'docs/data')
            for name in ('SPIKE_RESULT.md', 'ATTRIBUTION_AUDIT.md'):
                shutil.copyfile(ROOT / 'docs' / name, checkout / 'docs' / name)
            module.ROOT = checkout
            self.assertFalse((checkout / '.env').exists())
            self.assertFalse((checkout / 'data/raw').exists())
            destination = checkout / 'reproduced/docs'
            module.reproduce(destination)
            for name in ('summary.json', 'swaps.csv', 'accounts.csv', 'evidence.json',
                         'sensitivity.json', 'sensitivity.csv', 'account-persistence.csv',
                         'durability-inputs.json', 'economic-baseline.json', 'headline.txt', 'stress-evaluation.json'):
                self.assertEqual((ROOT / 'docs/data' / name).read_text(encoding='utf-8'),
                                 (destination / 'data' / name).read_text(encoding='utf-8'), name)
            manifest = json.loads((checkout / 'snapshots/manifest.json').read_text())
            self.assertEqual(manifest['transactions'], 1333)
            self.assertEqual(manifest['swaps'], 555)


if __name__ == '__main__':
    unittest.main()
