import unittest
import os
import logging

from ibrokersmargin import parse_csv_margin_data, get_margin_data


class MarginReportTestCase(unittest.TestCase):

    def setUp(self):
        self.tree = None
        example_file_path = os.path.abspath(os.sep.join(['tests-data', 'U1760542.margin.20170628.csv']))
        logging.info('loading example result file: {}'.format(example_file_path))
        self.ib_data = parse_csv_margin_data(example_file_path)

    def test_ib_data(self):
        expected_keys = ['Account', 'MarginSummary', 'MarginDetailSecuritiesRulesBased',
                         'MarginDetailSecuritiesRiskBased', 'MarginDetailFuturesRiskBased',
                         'PortfolioMarginDetail', 'SpanMarginOverview']
        self.assertListEqual(expected_keys, list(self.ib_data.keys()))

    def test_margin_summary(self):
        margin_summary = self.ib_data['MarginSummary'].set_index('Parameter')['Total']
        margin_data = get_margin_data(self.ib_data)
        net_liquidation_value = margin_data['net_liquidation_value']
        maintenance_margin_requirement = margin_data['maintenance_margin_requirement']
        initial_margin_requirement = margin_data['initial_margin_requirement']
        cash_value = margin_data['cash_value']
        available_funds = net_liquidation_value - initial_margin_requirement
        excess_liquidity = net_liquidation_value - maintenance_margin_requirement
        margin_ratio = initial_margin_requirement / net_liquidation_value
        self.assertEqual(net_liquidation_value, 10285630)
        self.assertEqual(cash_value, 5158671)
        self.assertEqual(initial_margin_requirement, 4533994)
        self.assertEqual(maintenance_margin_requirement, 3815870)
        self.assertEqual(margin_data['as_of_date'], '2017-06-28T07:40:42Z')
        self.assertEqual(margin_data['base_currency'], 'EUR')
        self.assertEqual(round(float(margin_summary['AvailableFunds'])), available_funds)
        self.assertEqual(round(float(margin_summary['ExcessLiquidity'])), excess_liquidity)
        self.assertAlmostEqual(float(margin_summary['Margin Ratio (%)']) / 100, margin_ratio, places=2)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    unittest.main()
