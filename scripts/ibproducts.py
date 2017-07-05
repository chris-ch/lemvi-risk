import logging
import argparse
from datetime import datetime, timedelta
from pprint import pprint

from webscrapetools import urlcaching

from ibrokersflex import parse_flex_positions
from searchproduct import search_product, load_search_page


def from_ib_date(date_ddmmYYYY):
    if date_ddmmYYYY == '-':
        return None

    return datetime.strptime(date_ddmmYYYY, '%d/%m/%Y')


def main(args):
    urlcaching.set_cache_path(args.cache_path, expiry_days=300)
    deadline = datetime.today()
    if args.deadline:
        deadline = datetime.strptime(args.deadline, '%Y-%m-%d')

    deadline = deadline - timedelta(days=args.warning_period)

    with open(args.ibrokers_data) as ibrokers_flex:
        flex_positions = parse_flex_positions(ibrokers_flex.read())
        for account in flex_positions:
            positions = flex_positions[account]
            print(account)
            for product_code in positions:
                if positions[product_code]['assetCategory'] == 'FUT':
                    page_content = load_search_page(product_code)
                    product_details = search_product(page_content)
                    product_description = product_details['Contract Information']['Description/Name']
                    product_name = positions[product_code]['description']
                    expiration_date = from_ib_date(product_details['Futures Features']['Expiration Date'])
                    first_notice_date = from_ib_date(product_details['Futures Features']['First Notice Date'])
                    last_trading_date = from_ib_date(product_details['Futures Features']['Last Trading Date'])
                    product_data = {
                        'product_description': product_description,
                        'product_name': product_name,
                        'expiration_date': expiration_date,
                        'first_notice_date': first_notice_date,
                        'last_trading_date': last_trading_date
                    }
                    if (first_notice_date and deadline >= first_notice_date) or (last_trading_date and deadline >= last_trading_date):
                        pprint(product_data)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler = logging.FileHandler('ibproducts.log', mode='w')
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    logging.info('starting script')
    parser = argparse.ArgumentParser(description='Looking up product information on IBrokers website',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--ibrokers-data', type=str, help='Location of InteractiveBrokers Flex response', required=True)
    parser.add_argument('--cache-path', type=str, help='Cache path for InteractiveBorkers response', default='.')
    parser.add_argument('--deadline', type=str, help='Deadline for checking expiring products (YYYY-MM-DD format)')
    parser.add_argument('--warning-period', type=int, help='Maximum number of days before deadline', default=3)

    args = parser.parse_args()
    main(args)
