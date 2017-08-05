import json
import logging
import os
import unittest
from datetime import date

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

    def test_drawdown(self):
        hwms, drawdowns = compute_high_watermark(self.flows, self.navs)
        account = 'U1812119'
        self.assertEqual(hwms[account].loc[date(2017, 6, 28)], 1951550)
        self.assertEqual(hwms[account].loc[date(2017, 6, 29)], 1801550)
        self.assertEqual(hwms[account].loc[date(2017, 8, 2)], 2101550)
        self.assertEqual(drawdowns[account].loc[date(2017, 8, 2)], -501012)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    unittest.main()
