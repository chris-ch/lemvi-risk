from xml.etree import ElementTree
from datetime import date


def parse_flex_result(content):
    """
    
    :param content: xml IBrokers Flex string
    :return: dict key-ed by account id
    """
    accounts = dict()
    tree = ElementTree.fromstring(content)
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
        cash_node_pattern = "./EquitySummaryInBase/EquitySummaryByReportDateInBase[@reportDate='{}']".format(date_yyyymmdd)
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
            'margin': float(cash_value) / float(nav_end)
        }

    return accounts
