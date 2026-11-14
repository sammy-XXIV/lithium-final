"""The analyst's data-only build must work without raw snapshots or local caches."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublishedReproductionTests(unittest.TestCase):
    def run_build(self, mutate=None):
        script = ROOT / 'tools/reproduce_tables.py'
        self.assertTrue(script.exists(), 'Missing data-only reproduction command')
        spec = importlib.util.spec_from_file_location('reproduce_tables', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / 'checkout'
            shutil.copytree(ROOT / 'docs', checkout / 'docs')
            self.assertFalse((checkout / 'snapshots').exists())
            self.assertFalse((checkout / 'queries').exists())
            self.assertFalse((checkout / 'data').exists())
            if mutate:
                mutate(checkout / 'docs/data')
            output = checkout / 'reproduced/docs'
            log = io.StringIO()
            with redirect_stdout(log):
                result = module.reproduce(checkout / 'docs/data', output)
            return result, log.getvalue(), (output / 'index.html').exists()

    def test_data_only_checkout_regenerates_every_output(self):
        success, log, page = self.run_build()
        self.assertTrue(success, log)
        self.assertTrue(page)
        self.assertIn('PASS summary.json', log)
        self.assertIn('PASS index.html', log)
        self.assertIn('PASS data/coverage-date.csv', log)

    def test_changed_summary_fails(self):
        def mutate(data):
            path = data / 'summary.json'
            summary = json.loads(path.read_text(encoding='utf-8'))
            summary['count'] += 1
            path.write_text(json.dumps(summary), encoding='utf-8')
        success, log, _ = self.run_build(mutate)
        self.assertFalse(success)
        self.assertIn('FAIL summary.json: count', log)

    def test_stale_table_fails_even_when_summary_matches(self):
        def mutate(data):
            path = data / 'coverage-date.csv'
            path.write_bytes(path.read_bytes().replace(b'2026-09-16', b'2026-09-17', 1))
        success, log, _ = self.run_build(mutate)
        self.assertFalse(success)
        self.assertIn('FAIL data/coverage-date.csv', log)

    def test_extra_nullable_summary_field_is_reported_as_mismatch(self):
        def mutate(data):
            path = data / 'summary.json'
            summary = json.loads(path.read_text(encoding='utf-8'))
            summary['unexpected_null'] = None
            path.write_text(json.dumps(summary), encoding='utf-8')
        success, log, _ = self.run_build(mutate)
        self.assertFalse(success)
        self.assertIn('FAIL summary.json: unexpected_null', log)


if __name__ == '__main__':
    unittest.main()
