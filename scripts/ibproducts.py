import logging
import argparse
import os
from collections import defaultdict
from datetime import datetime, timedelta

from webscrapetools import urlcaching

from ibrokersflex import parse_flex_positions
from searchproduct import search_product, load_search_page


def from_ib_date(date_ddmmYYYY):
    if date_ddmmYYYY == '-':
        return None

    return datetime.strptime(date_ddmmYYYY, '%d/%m/%Y')


def main(args):
    os.makedirs(args.output_path, exist_ok=True)
    urlcaching.set_cache_path(args.cache_path, expiry_days=300)
    deadline = datetime.today()
    if args.deadline:
        deadline = datetime.strptime(args.deadline, '%Y-%m-%d')

    deadline = deadline + timedelta(days=args.warning_period)

    with open(args.ibrokers_data) as ibrokers_flex:
        flex_positions = parse_flex_positions(ibrokers_flex.read())
        expiring_products = defaultdict(list)
        for account in flex_positions:
            positions = flex_positions[account]
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

                    first_notice_date_past = False
                    if first_notice_date:
                        first_notice_date_past = deadline >= first_notice_date

                    last_trading_date_past = False
                    if last_trading_date:
                        last_trading_date_past = deadline >= last_trading_date

                    if first_notice_date_past or last_trading_date_past:
                        expiring_products[account].append(product_data)

        output_message = ''
        for account in expiring_products:
            output_message += '*Account {}*\n'.format(account)
            products = expiring_products[account]
            for product in products:
                first_notice = '-'
                if product['first_notice_date']:
                    first_notice = product['first_notice_date'].strftime('%Y-%m-%d')

                last_trading = '-'
                if product['last_trading_date']:
                    last_trading = product['last_trading_date'].strftime('%Y-%m-%d')

                output_message += '{product_name} - {product_description}: last trading {last_trading_date} / first notice {first_notice_date}\n'.format(
                    product_name=product['product_name'],
                    product_description=product['product_description'],
                    first_notice_date=first_notice,
                    last_trading_date=last_trading,
                )

        output_target = os.path.abspath(os.sep.join([args.output_path, args.output_file]))
        logging.info('writing results to {}'.format(output_target))
        with open(output_target, 'w') as output_file:
            output_file.write(output_message)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
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
    parser.add_argument('--warning-period', type=int, help='Maximum number of days before deadline', default=0)
    parser.add_argument('--output-path', type=str, help='output path', default='.')
    parser.add_argument('--output-file', type=str, help='output file', default='ibproducts.txt')

    args = parser.parse_args()
    try:
        main(args)

    except:
        logging.fatal('A fatal error occured')
        raise

