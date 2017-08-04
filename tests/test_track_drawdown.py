import json
import unittest
import os
import logging
from datetime import datetime

import pandas
from decimal import Decimal


def to_decimal(value):
    if type(value) == str:
        value = value.replace(',', '').replace("'", '')

    return Decimal(value)


def extract_flows(flows_data):
    concat_flows = pandas.DataFrame()
    for account, flows in flows_data.items():
        converted_flows = list()
        for flow in flows:
            print(flow)
            converted_flow = {
                'Date': datetime.strptime(flow['Date'], '%Y-%m-%d'),
                'NAV UK': to_decimal(flow['NAV UK']),
                'NAV US': to_decimal(flow['NAV US']),
                'Total NAV': to_decimal(flow['Total NAV']),
            }
            converted_flows.append(converted_flow)

        account_flows = pandas.DataFrame(converted_flows)
        account_flows['account'] = account
        concat_flows = pandas.concat([concat_flows, account_flows])

    return concat_flows


class TrackDrawdownTestCase(unittest.TestCase):

    def setUp(self):
        example_navs_file_path = os.path.abspath(os.sep.join(['tests-data', 'google-navs-data.json']))
        logging.info('loading example navs file: {}'.format(example_navs_file_path))
        with open(example_navs_file_path, 'r') as navs_file:
            self.navs = pandas.DataFrame(json.load(navs_file))

        example_flows_file_path = os.path.abspath(os.sep.join(['tests-data', 'google-flows-data.json']))
        logging.info('loading example flows file: {}'.format(example_flows_file_path))
        with open(example_flows_file_path, 'r') as flows_file:
            flows_data = json.load(flows_file)
            concat_flows = extract_flows(flows_data)

        self.flows = concat_flows

    def test_drawdown(self):
        print(self.flows.head())
        print(self.navs.head())

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    unittest.main()
