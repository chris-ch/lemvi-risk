import json
import unittest
import os
import logging
from datetime import datetime

import pandas
from decimal import Decimal

from matplotlib import pyplot


def to_decimal(value):
    if type(value) == str:
        value = value.replace(',', '').replace("'", '')

    return float(Decimal(value))


def extract_flows(flows_data):
    converted_flows = list()
    for row in flows_data:
        flow_data = {'Date': datetime.strptime(row['Date'], '%Y-%m-%d').date()}
        for key in row:
            if key == 'Date':
                continue

            flow_data[key] = to_decimal(row[key])

        converted_flows.append(flow_data)

    flows = pandas.DataFrame(converted_flows).set_index('Date').sort_index(ascending=True)
    return flows


def extract_navs(navs_data):
    concat_navs = pandas.DataFrame()
    for account, nav_data in navs_data.items():
        converted_flows = list()
        for item in nav_data:
            converted_flow = {
                'Date': datetime.strptime(item['Date'], '%Y-%m-%d').date(),
                'NAV UK': to_decimal(item['NAV UK']),
                'NAV US': to_decimal(item['NAV US']),
                'Total NAV': to_decimal(item['Total NAV']),
            }
            converted_flows.append(converted_flow)

        account_navs = pandas.DataFrame(converted_flows)
        account_navs['account'] = account
        concat_navs = pandas.concat([concat_navs, account_navs])

    navs = concat_navs.pivot(index='Date', columns='account', values='Total NAV').sort_index(ascending=True)
    return navs


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
        # HWM = IF(NAV_ADJ >= NAV_PREV, NAV, HWM_ADJ)
        # NAV_ADJ = NAV + FLOW
        # HWM_ADJ = HWM_UNADJ_PREV + FLOW
        (flows, navs) = self.flows.align(self.navs)
        cum_flows = flows.fillna(0).cumsum()
        navs_adj = navs - cum_flows
        hwm = navs_adj.cummax().unstack()
        navs = navs.unstack()
        navs_adj = navs_adj.unstack()
        cum_flows = cum_flows.unstack()
        drawdowns = navs_adj - hwm
        hwm_adj = navs - drawdowns

        account = 'U1812119'
        print(navs_adj.loc[account].head())
        print(hwm.loc[account].head())
        navs.loc[account].plot()
        hwm_adj.loc[account].plot()
        cum_flows.loc[account].plot()
        pyplot.show()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    unittest.main()
