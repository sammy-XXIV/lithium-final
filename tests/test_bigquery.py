"""Keep warehouse execution statuses and sampling denominators distinct."""
import json
import tempfile
import unittest
from pathlib import Path


class BigQueryTests(unittest.TestCase):
    def test_imported_inventory_preserves_statuses_and_per_window_counts(self):
        from solverline.bigquery import load_inventory, render_inventory
        evidence = load_inventory()
        self.assertEqual(evidence['totals'], {
            'SUCCESS_VALUE': 9280, 'FAILURE': 359, 'SUCCESS_RECEIPT_ID': 11})
        self.assertEqual(len(evidence['windows']), 24)
        self.assertEqual(sum(w['intents_executed'] for w in evidence['windows']), 1671)
        self.assertEqual(sum(w['token_diff'] for w in evidence['windows']), 1460)
        with tempfile.TemporaryDirectory() as tmp:
            section = render_inventory(evidence, Path(tmp))
            self.assertIn('not swaps', section)
            self.assertIn('SUCCESS_RECEIPT_ID', section)
            self.assertIn('12,748,608,695', section)
            self.assertIn('GROUP BY observed_date', section)
            data = Path(tmp) / 'data/bigquery'
            self.assertEqual(json.loads((data / 'results.json').read_text()), evidence['rows'])
            self.assertEqual(json.loads((data / 'job.json').read_text())['status']['state'], 'DONE')

    def test_bad_job_or_modified_results_cannot_silently_become_evidence(self):
        from solverline.bigquery import load_inventory
        from solverline.pull_explorer import ROOT
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'queries'
            shutil.copytree(ROOT / 'queries', source)
            p = source / 'results/02_sample_window_event_inventory.json'
            rows = json.loads(p.read_text())
            rows[0]['event_log_count'] = '999999'
            p.write_text(json.dumps(rows))
            with self.assertRaisesRegex(ValueError, 'hash'):
                load_inventory(source)
