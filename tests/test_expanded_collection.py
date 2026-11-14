"""An expanded cohort must never reuse a different window or overwrite baseline."""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class ExpandedCollectionTests(unittest.TestCase):
    def test_expanded_rebuild_rejects_explicit_baseline_destinations(self):
        from solverline.rebuild import run
        from solverline.pull_explorer import ROOT
        with patch('solverline.rebuild.resolve', side_effect=AssertionError('Must reject before loading/writing')):
            with self.assertRaisesRegex(ValueError, 'baseline'):
                run(explorer_directory=ROOT / 'data/raw/explorer-expanded',
                    derived_directory=ROOT / 'data/derived', docs_directory=ROOT / 'docs')

    def test_changed_config_cannot_fetch_into_baseline_cache(self):
        from solverline.rebuild import run
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'expanded.json'
            config.write_text(json.dumps({'window_minutes':60}))
            with patch('solverline.rebuild.subprocess.run', side_effect=AssertionError('Must reject before fetching')):
                with self.assertRaisesRegex(ValueError, 'isolated'):
                    run(config=config, offline=False)

    def test_expanded_rebuild_cannot_silently_replace_baseline_outputs(self):
        from solverline.rebuild import run
        with patch('solverline.rebuild.resolve') as resolve:
            with self.assertRaisesRegex(ValueError, 'isolated'):
                run(explorer_directory=Path('isolated-cache'))
            resolve.assert_not_called()

    def test_expansion_is_resumable_and_scope_changes_are_rejected(self):
        from solverline.expand_sample import collect
        with tempfile.TemporaryDirectory() as tmp:
            config, out = Path(tmp) / 'scope.json', Path(tmp) / 'expanded'
            spec = dict(dates=['2026-11-11'], slots_utc=['00:00'], window_minutes=20, statuses='SUCCESS', page_size=1000)
            config.write_text(json.dumps(spec))
            row = dict(depositAddress='sample', createdAt='2026-11-11T00:05:00.000Z', status='SUCCESS')
            with patch('solverline.expand_sample.pull_window', return_value=([row], True)) as pull:
                collect(config, out, {'EXPLORER_JWT':'test'})
                collect(config, out, {'EXPLORER_JWT':'test'})
                self.assertEqual(pull.call_count, 1)
            saved = json.loads((out / '20261111T0000.json').read_text())
            self.assertEqual(saved['count'], 1)
            self.assertEqual(saved['end'], '2026-11-11T00:20:00.000Z')
            spec['window_minutes'] = 60
            config.write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError, 'scope'):
                collect(config, out, {'EXPLORER_JWT':'test'})

    def test_nonadvancing_pagination_is_not_a_complete_expanded_window(self):
        from solverline.expand_sample import collect
        with tempfile.TemporaryDirectory() as tmp:
            config, out = Path(tmp) / 'scope.json', Path(tmp) / 'expanded'
            config.write_text(json.dumps(dict(dates=['2026-11-11'], slots_utc=['00:00'], window_minutes=20, statuses='SUCCESS', page_size=1000)))
            with patch('solverline.expand_sample.pull_window', return_value=([], False)):
                with self.assertRaisesRegex(RuntimeError, 'incomplete'):
                    collect(config, out, {'EXPLORER_JWT':'test'})
            self.assertFalse(json.loads((out / '20261111T0000.json').read_text())['complete'])
