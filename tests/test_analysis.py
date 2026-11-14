"""Catch false precision, denominator loss and incorrectly narrow bounds."""
import itertools
import unittest
from decimal import Decimal as D


class AnalysisTests(unittest.TestCase):
    def test_known_and_unknown_volume_bounds(self):
        from solverline.analyze import concentration
        result = concentration([D('30'), D('20')], D('50'))
        self.assertEqual(result['top1_lower'], '0.3')
        self.assertEqual(result['top1_upper'], '0.8')
        self.assertEqual(result['hhi_lower'], '0.13')
        self.assertEqual(result['hhi_upper'], '0.68')
        self.assertEqual(result['subset_top1'], '0.6')
        unknown = concentration([], D('100'))
        self.assertIsNone(unknown['subset_hhi'])
        self.assertEqual((unknown['hhi_lower'], unknown['hhi_upper']), ('0', '1'))
        self.assertIsNone(concentration([], D('0'))['hhi_lower'])
        known = concentration([D('30'), D('20')], D('0'))
        self.assertEqual(known['hhi_lower'], known['hhi_upper'])

    def test_small_finite_assignments_fit_conservative_intervals(self):
        from solverline.analyze import concentration
        bounds = concentration([D('3'), D('2')], D('3'))
        for assignment in itertools.product(range(4), repeat=2):
            accounts = [D('3'), D('2'), D(0), D(0)]
            for owner, amount in zip(assignment, (D(1), D(2))):
                accounts[owner] += amount
            accounts.sort(reverse=True)
            top1 = accounts[0] / 8
            hhi = sum(a * a for a in accounts) / 64
            self.assertTrue(D(bounds['top1_lower']) <= top1 <= D(bounds['top1_upper']))
            self.assertTrue(D(bounds['hhi_lower']) <= hhi <= D(bounds['hhi_upper']))

    def test_missing_usd_is_excluded_and_unknown_is_retained(self):
        from solverline.analyze import aggregate
        rows = [{'amountInUsd': '30', 'settlement_class': 'public', 'filler_account': 'maker', 'attribution_status': 'attributed'},
                {'amountInUsd': '70', 'settlement_class': 'confidential_treasury', 'filler_account': None},
                {'amountInUsd': 'NaN', 'settlement_class': 'unresolved'},
                {'amountInUsd': None, 'settlement_class': 'unresolved'},
                {'amountInUsd': '-5', 'settlement_class': 'unresolved'}]
        result = aggregate(rows)
        self.assertEqual(result['total_usd'], '100')
        self.assertEqual(result['invalid_usd_count'], 3)
        self.assertEqual(result['attributable_share'], '0.3')
        self.assertEqual(result['confidential_treasury_share'], '0.7')
        self.assertEqual(result['unknown_usd'], '70')
        self.assertEqual(result['hhi_lower'], '0.09')
        self.assertEqual(result['hhi_upper'], '1')


if __name__ == '__main__':
    unittest.main()
