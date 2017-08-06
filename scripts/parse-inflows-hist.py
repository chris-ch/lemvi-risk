import argparse
import logging
import pandas
from datetime import datetime
import lxml.etree
from decimal import Decimal


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
            for line in statement.findall('.//Transfers/Transfer'):
                date = datetime.strptime(line.get('date'), '%Y%m%d').date()
                currency = line.get('currency')
                amount_cash = Decimal(line.get('cashTransfer'))
                amount_position = Decimal(line.get('positionAmountInBase'))
                if account_id.lower().endswith('f'):
                    account_id = account_id[:-1]

                transfer = {'account': account_id, 'date': date, 'amount_cash': amount_cash,
                            'amount_position': amount_position, 'amount': amount_cash + amount_position}
                transfers.append(transfer)

    flat_transfers = pandas.DataFrame(transfers)
    flat_transfers.sort_values(['account', 'date'], inplace=True)
    flat_transfers[['account', 'date', 'amount_cash', 'amount_position', 'amount']].to_csv('flat-transfers.csv', index=False)
    transfers_flat = flat_transfers.groupby(['account', 'date']).sum()
    transfers_df = transfers_flat.unstack(level=0, fill_value=0)['amount']
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
