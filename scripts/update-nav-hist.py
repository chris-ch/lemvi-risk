import argparse
import json
import logging
import os
from datetime import datetime

import gservices
from ibrokersflex import parse_flex_accounts


def from_excel_datetime(excel_date):
    return datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(excel_date) - 2)


def from_excel_date(excel_date):
    return from_excel_datetime(excel_date).date()


def upload_navs(accounts, google_sheet_id, svc_sheet):
    workbook = svc_sheet.open_by_key(google_sheet_id)
    for account in [name for name in accounts if not name.endswith("F")]:
        if account not in [tab.title for tab in workbook.worksheets()]:
            column_names = ['Date', 'NAV US', 'NAV UK', 'Total NAV']
            sheet = workbook.add_worksheet(account, rows=2, cols=len(column_names))

        else:
            sheet = workbook.worksheet_by_title(account)

        account_data = accounts[account]
        last_update_cell = sheet.cell('A2')
        last_update = datetime.strptime(last_update_cell.value, '%Y-%m-%d').date()
        update_date = account_data['as_of_date']
        if last_update < update_date:
            nav_us = account_data['nav_end']
            account_uk = account + 'F'
            if account_uk in accounts:
                nav_uk = accounts[account_uk]['nav_end']

            else:
                nav_uk = 0

            values = [update_date.strftime('%Y-%m-%d'), float(nav_us), float(nav_uk), float(nav_us + nav_uk)]
            sheet.insert_rows(row=1, number=1, values=[values])
            logging.info('updated account {} as of {}'.format(account, last_update))

        else:
            logging.info('account {} already up to date {}'.format(account, last_update))


def main(args):
    full_config_path = os.path.abspath(args.config)
    logging.info('using config file "{}"'.format(full_config_path))
    with open(full_config_path, 'r') as config_file:
        config = json.load(config_file)

    full_flex_path = os.path.abspath(args.file_ibrokers_flex)
    logging.info('using InteractiveBrokers flex file "{}"'.format(full_flex_path))
    with open(full_flex_path, 'r') as ibrokers_response_file:
        ibrokers_response = ibrokers_response_file.read()
        accounts = parse_flex_accounts(ibrokers_response)
        secrets_file_path = os.path.abspath(args.file_secret)
        logging.info('using secrets file "{}"'.format(secrets_file_path))
        with open(secrets_file_path) as json_data:
            secrets_content = json.load(json_data)
            google_credential = secrets_content['google.credential']
            authorized_http, credentials = gservices.authorize_services(google_credential)
            svc_sheet = gservices.create_service_sheets(credentials)
            google_sheet_nav_id = config['google.sheet.navs.id']
            upload_navs(accounts, google_sheet_nav_id, svc_sheet)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    logging.getLogger('requests').setLevel(logging.WARNING)
    file_handler = logging.FileHandler('update-nav-hist.log', mode='w')
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    parser = argparse.ArgumentParser(description='NAV history update.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                     )
    parser.add_argument('--file-ibrokers-flex', type=str, help='InteractiveBrokers Flex response')
    parser.add_argument('--file-secret', type=str, help='file including secret connection data', default='secrets.json')
    parser.add_argument('--config', type=str, help='file including secret connection data', default='config.json')

    args = parser.parse_args()
    main(args)
