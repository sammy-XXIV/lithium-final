"""Catch false offline completion, lost evidence and unsafe dashboard content."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class PipelineTests(unittest.TestCase):
    def test_due_diligence_does_not_invent_bounds_without_valid_usd(self):
        from solverline.analyze import aggregate
        from solverline.build_dashboard import decision_panel
        panel = decision_panel(aggregate([]))
        self.assertIn('Unavailable', panel)

    def test_dashboard_is_deterministic_and_preserves_evidence(self):
        from solverline.analyze import analyze
        from solverline.build_dashboard import build_dashboard
        row = {'depositAddress': 'sample', 'createdAt': '2026-09-16T00:01:00Z',
               'sample_window': '2026-09-16T00:00:00.000Z', 'source_file': 'window.json',
               'amountInUsd': '10.50', 'originAsset': 'A', 'destinationAsset': 'B',
               'settlement_class': 'unresolved', 'attribution_status': 'unattributed',
               'filler_account': None, 'rpc_complete': False, 'tx_count': 1, 'tx_available': 0,
               'reason': 'missing_or_failed_rpc', 'evidence': [], 'nearTxHashes': ['tx'],
               'referral': '<script>alert(1)</script>', 'appFees': [{'recipient': 'a'}, {'recipient': 'b'}, {'recipient': 'a'}]}
        manifest = {'tx_total': 1, 'tx_available': 0, 'receipt_run_complete': False,
                    'windows': [{'start': row['sample_window'], 'end': '2026-09-16T00:02:00.000Z'}],
                    'bigquery': {'status': 'incomplete'}}
        with tempfile.TemporaryDirectory() as tmp:
            derived, docs = Path(tmp) / 'derived', Path(tmp) / 'docs'
            report = analyze([row], manifest, derived)
            self.assertEqual(report['distributions']['fee-recipients'][0]['share'], '1')
            self.assertEqual(len(report['distributions']['fee-recipients']), 2)
            build_dashboard(report, derived, docs)
            first = (docs / 'index.html').read_bytes()
            build_dashboard(report, derived, docs)
            self.assertEqual(first, (docs / 'index.html').read_bytes())
            html = first.decode()
            self.assertIn('BigQuery', html)
            self.assertIn('incomplete', html.lower())
            self.assertIn('Provisional snapshot', html)
            self.assertNotIn('<script>alert(1)</script>', html)
            self.assertIn('missing_or_failed_rpc', (docs / 'data/evidence.json').read_text())
            self.assertIn('10.5', (docs / 'data/swaps.csv').read_text())

    def test_offline_rebuild_never_fetches_and_rejects_missing_receipts(self):
        from solverline.rebuild import run
        with patch('urllib.request.urlopen', side_effect=AssertionError('offline used network')):
            with patch('solverline.rebuild.resolve', return_value=([], {'receipt_run_complete': False})):
                with self.assertRaisesRegex(RuntimeError, 'receipt'):
                    run(offline=True)


if __name__ == '__main__':
    unittest.main()
