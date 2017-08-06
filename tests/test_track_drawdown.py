import json
import logging
import os
import unittest
from datetime import date

from decimal import Decimal

from risklimits import extract_flows, extract_navs, compute_high_watermark


class TrackDrawdownTestCase(unittest.TestCase):

    def setUp(self):
        example_navs_file_path = os.path.abspath(os.sep.join(['tests-data', 'google-navs-data.json']))
        logging.info('loading example navs file: {}'.format(example_navs_file_path))
        with open(example_navs_file_path, 'r') as navs_file:
            navs_data = json.load(navs_file)
            self.navs = extract_navs(navs_data)

        example_flows_file_path = os.path.abspath(os.sep.join(['tests-data', 'google-flows-data.json']))
        logging.info('loading example flows file: {}'.format(example_flows_file_path))
        with open(example_flows_file_path, 'r') as flows_file:
            flows_data = json.load(flows_file)
            self.flows = extract_flows(flows_data)

    def test_drawdown_119(self):
        hwms, drawdowns = compute_high_watermark(self.flows, self.navs)
        account = 'U1812119'
        self.assertEqual(hwms[account].loc[date(2017, 6, 28)], 1951550)
        self.assertEqual(hwms[account].loc[date(2017, 6, 29)], 1801550)
        self.assertEqual(hwms[account].loc[date(2017, 8, 2)], 2101550)
        self.assertEqual(drawdowns[account].loc[date(2017, 8, 2)], -501012)

    def test_drawdown_955(self):
        hwms, drawdowns = compute_high_watermark(self.flows, self.navs)
        account = 'U1812955'
        self.assertEqual(hwms[account].loc[date(2017, 3, 30)], Decimal("2756679"))
        self.assertEqual(hwms[account].loc[date(2017, 3, 31)], Decimal("1966572.0087808"))
        self.assertEqual(hwms[account].loc[date(2017, 4, 3)], Decimal("1966572.0087808"))
        self.assertEqual(drawdowns[account].loc[date(2017, 3, 30)], Decimal("-336642"))
        self.assertEqual(drawdowns[account].loc[date(2017, 3, 31)], Decimal("-343466.0087808"))
        self.assertEqual(drawdowns[account].loc[date(2017, 4, 3)], Decimal("-376385.0087808"))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    unittest.main()
