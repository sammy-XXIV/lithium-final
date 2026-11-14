"""Sensitivity checks must remove whole swaps and retain unknown volume."""
import copy
import unittest


class SensitivityTests(unittest.TestCase):
    def test_removals_recompute_denominators_and_preserve_unknowns(self):
        from solverline.sensitivity import sensitivity
        def row(amount, account, date, identity):
            return {'amountInUsd': str(amount), 'filler_account': account,
                    'settlement_class': 'public' if account else 'unresolved',
                    'attribution_status': 'attributed' if account else 'unattributed',
                    'sample_window': date + 'T00:00:00Z', 'createdAt': date + 'T00:00:01Z',
                    'depositAddress': identity, 'originAsset': 'A', 'destinationAsset': 'B'}
        rows = [row(60, None, '2026-09-16', 'a'), row(30, 'maker-a', '2026-09-16', 'b'),
                row(10, 'maker-b', '2026-09-24', 'c')]
        original = copy.deepcopy(rows)
        result = sensitivity(rows)
        cases = {r['scenario']: r for r in result['scenarios']}
        self.assertEqual(cases['exclude_largest_1_all']['total_usd'], '40')
        self.assertEqual(cases['exclude_largest_1_all']['unknown_usd'], '0')
        self.assertEqual(cases['exclude_largest_1_attributed']['total_usd'], '70')
        self.assertEqual(cases['exclude_largest_1_attributed']['unknown_usd'], '60')
        self.assertEqual(cases['exclude_date_2026-09-16']['total_usd'], '10')
        self.assertEqual(result['accounts'][0]['observed_dates'], 1)
        self.assertEqual(rows, original)
        self.assertEqual(result, sensitivity(list(reversed(rows))))

    def test_empty_sample_has_no_fabricated_concentration(self):
        from solverline.sensitivity import sensitivity
        result = sensitivity([])
        self.assertIsNone(result['scenarios'][0]['subset_top3'])
        self.assertIsNone(result['largest_attributed_swap_share'])


if __name__ == '__main__':
    unittest.main()
