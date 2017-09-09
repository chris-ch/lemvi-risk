import logging
from decimal import Decimal
from datetime import datetime

import pandas


def _to_decimal(value):
    if type(value) == str:
        value = value.replace(',', '').replace("'", '')

        if value.strip() == '':
            return Decimal(0)

    return Decimal(value)


def extract_flows(flows_data):
    """
    Flows records from Google sheet.
    :param flows_data:
    :return:
    """
    converted_flows = list()
    for row in flows_data:
        if 'date' in row:
            row_date = row['date']

        else:
            row_date = row['Date']

        flow_data = {'Date': datetime.strptime(row_date, '%Y-%m-%d').date()}
        for key in row:
            if key.lower() == 'date':
                continue

            flow_data[key] = _to_decimal(row[key])

        converted_flows.append(flow_data)

    flows = pandas.DataFrame(converted_flows).set_index('Date').sort_index(ascending=True)
    return flows


def extract_navs(navs_data):
    """
    dict() of Navs records from Google sheet.
    :param navs_data:
    :return:
    """
    concat_navs = pandas.DataFrame()
    for account, nav_data in navs_data.items():
        converted_flows = list()
        logging.info('processing {} - {}'.format(account, nav_data))
        for item in nav_data:
            if len(item) == 0:
                # ignoring empty lines
                continue

            converted_flow = {
                'Date': datetime.strptime(item['Date'], '%Y-%m-%d').date(),
                'NAV UK': _to_decimal(item['NAV UK']),
                'NAV US': _to_decimal(item['NAV US']),
                'Total NAV': _to_decimal(item['Total NAV']),
            }
            converted_flows.append(converted_flow)

        account_navs = pandas.DataFrame(converted_flows)
        account_navs['account'] = account
        concat_navs = pandas.concat([concat_navs, account_navs])

    navs = concat_navs.pivot(index='Date', columns='account', values='Total NAV').sort_index(ascending=True)
    return navs


def compute_high_watermark(flows, navs):
    """

    :param flows:
    :param navs:
    :return:
    """
    (aligned_flows, aligned_navs) = flows.align(navs)
    cum_flows = aligned_flows.fillna(0).cumsum()
    navs_adj = aligned_navs - cum_flows
    hwm = navs_adj.cummax().unstack()
    navs = aligned_navs.unstack()
    navs_adj = navs_adj.unstack()
    drawdowns = navs_adj - hwm
    hwm_adj = navs - drawdowns
    return hwm_adj.unstack().transpose(), drawdowns.unstack().transpose()
