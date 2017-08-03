from collections import OrderedDict

import io
from lxml import etree
from datetime import date
from datetime import datetime

from decimal import Decimal

import pandas


def parse_flex_accounts(content):
    """

    :param content: xml IBrokers Flex string
    :return: dict of account data key-ed by account id
    """
    accounts = dict()
    tree = build_tree_from_str(content)
    for node_account in tree.findall('FlexStatements/FlexStatement'):
        node_account_information = node_account.find('AccountInformation')
        node_change_in_nav = node_account.find('ChangeInNAV')

        date_yyyymmdd = node_account.get('toDate')
        as_of_date = date(int(date_yyyymmdd[:4]), int(date_yyyymmdd[4:6]), int(date_yyyymmdd[-2:]))
        account_alias = node_account_information.get('acctAlias')
        account_id = node_account_information.get('accountId')
        currency = node_account_information.get('currency')
        nav_change = int(float(node_change_in_nav.get('mtm')))
        nav_start = int(float(node_change_in_nav.get('startingValue')))
        nav_end = int(float(node_change_in_nav.get('endingValue')))
        cash_node_pattern = "./EquitySummaryInBase/EquitySummaryByReportDateInBase[@reportDate='{}']".format(
            date_yyyymmdd)
        cash_node = node_account.find(cash_node_pattern)
        cash_value = int(float(cash_node.get('cash')))
        accounts[account_id] = {
            'as_of_date': as_of_date,
            'account_alias': account_alias,
            'account_id': account_id,
            'currency': currency,
            'nav_change': nav_change,
            'nav_start': nav_start,
            'nav_end': nav_end,
            'cash': cash_value,
        }

    ordered_accounts = OrderedDict()
    for account_data in sorted(accounts.values(), key=lambda account: account['account_alias']):
        ordered_accounts[account_data['account_id']] = account_data

    return ordered_accounts


def parse_flex_flows(content, indicator='transfer', currency='EUR'):
    """

    :param content: xml IBrokers Flex string
    :param indicator: activity field to look for
    :param currency: currency to look for
    :return: dict of flows data key-ed by account id or None if no data available
    """
    transfers = list()
    tree = build_tree_from_str(content)
    for statement in tree.findall('FlexStatements/FlexStatement'):
        account_id = statement.get('accountId')
        date_yyyymmdd = statement.get('toDate')
        as_of_date = datetime.strptime(date_yyyymmdd, '%Y%m%d').date()
        for line in statement.findall('.//StatementOfFundsLine'):
            activity_description = line.get('activityDescription')
            if indicator.lower() in activity_description.lower():
                currency_line = line.get('currency')
                amount = Decimal(line.get('amount'))
                if account_id.endswith('F'):
                    account_id = account_id[:-1]

                transfer = {'account': account_id, 'date': as_of_date, 'currency': currency_line, 'amount': amount}
                transfers.append(transfer)

    if len(transfers) == 0:
        return None

    transfers_flat = pandas.DataFrame(transfers).groupby(['currency', 'account', 'date']).sum()
    if currency not in transfers_flat.index:
        return None

    transfers_df = transfers_flat.loc[currency].unstack(level=0, fill_value=0)['amount']
    transfers_df.sort_index(ascending=False)
    return transfers_df


def parse_flex_positions(content):
    """

    :param content: xml IBrokers Flex string
    :return: dict of open positions key-ed by account id
    """
    tree = build_tree_from_str(content)
    accounts = dict()
    for node_account in tree.findall('FlexStatements/FlexStatement'):
        account_id = node_account.get('accountId')
        open_position_elements = node_account.findall('OpenPositions/OpenPosition')
        accounts[account_id] = dict()
        for position_element in open_position_elements:
            position_data = dict()
            for key in position_element.keys():
                position_data[key] = position_element.get(key)

            accounts[account_id][position_data['conid']] = position_data

    return accounts


def build_tree_from_str(content):
    stream = io.StringIO()
    stream.write(content)
    stream.seek(0)
    tree = etree.parse(stream)
    return tree