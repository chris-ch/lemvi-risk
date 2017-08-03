import argparse
import logging
import pandas
from datetime import datetime
import lxml.etree
from decimal import Decimal


def from_excel_datetime(excel_date):
    return datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(excel_date) - 2)


def from_excel_date(excel_date):
    return from_excel_datetime(excel_date).date()


def main():
    parser = argparse.ArgumentParser(description='Parsing historical cash flows.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                     )
    parser.add_argument('input_file', type=str, help='xml input file')
    args = parser.parse_args()
    transfers = list()
    with open(args.input_file, 'r') as flows:
        tree = lxml.etree.parse(flows)
        for statement in tree.findall('//FlexStatement'):
            account_id = statement.get('accountId')
            for line in statement.findall('.//StatementOfFundsLine'):
                activity_description = line.get('activityDescription')
                if 'transfer' in activity_description.lower():
                    currency = line.get('currency')
                    date = datetime.strptime(line.get('date'), '%Y%m%d').date()
                    amount = Decimal(line.get('amount'))
                    if account_id.endswith('F'):
                        account_id = account_id[:-1]

                    transfer = {'account': account_id, 'date': date, 'currency': currency, 'amount': amount}
                    transfers.append(transfer)

    transfers_flat = pandas.DataFrame(transfers).groupby(['currency', 'account', 'date']).sum()
    transfers_df = transfers_flat.loc['EUR'].unstack(level=0, fill_value=0)['amount']
    print(transfers_df.head())
    transfers_df.to_csv('transfers.csv')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    logging.getLogger('requests').setLevel(logging.WARNING)
    file_handler = logging.FileHandler('update-nav-hist.log', mode='w')
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    main()
