import argparse
import json
import logging
import os
from datetime import datetime

import gspread

from gservices import authorize_services
from ibrokersflex import parse_flex_flows


def from_excel_datetime(excel_date):
    return datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(excel_date) - 2)


def from_excel_date(excel_date):
    return from_excel_datetime(excel_date).date()


def upload_flows(flow_date, flows, google_sheet_id, svc_sheet):
    workbook = svc_sheet.open_by_key(google_sheet_id)
    sheet = workbook.worksheet('Flows EUR')
    header = sheet.row_values(1)
    accounts = header[1:]
    last_row = sheet.row_values(2)
    last_date = datetime.strptime(last_row[0], '%Y-%m-%d').date()
    if flow_date > last_date:
        account_positions = {account: (count + 2) for count, account in enumerate(accounts) if account != ''}
        new_row = [0] * len(last_row)
        new_row[0] = flow_date
        for account in flows:
            new_row[account_positions[account]] = flows[account]

        sheet.insert_row(new_row, index=2)

    else:
        logging.info('Google flows sheet already up to date')


def main(args):
    full_config_path = os.path.abspath(args.config)
    logging.info('using config file "{}"'.format(full_config_path))
    with open(full_config_path, 'r') as config_file:
        config = json.load(config_file)

    full_flex_path = os.path.abspath(args.file_ibrokers_flex)
    logging.info('using InteractiveBorkers flex file "{}"'.format(full_flex_path))
    with open(full_flex_path, 'r') as ibrokers_response_file:
        ibrokers_response = ibrokers_response_file.read()
        secrets_file_path = os.path.abspath(args.file_secret)
        logging.info('using secrets file "{}"'.format(secrets_file_path))
        with open(secrets_file_path) as json_data:
            secrets_content = json.load(json_data)
            google_credential = secrets_content['google.credential']
            authorized_http, credentials = authorize_services(google_credential)
            svc_sheet = gspread.authorize(credentials)
            google_sheet_flow_id = config['google.sheet.flows.id']
            flows = parse_flex_flows(ibrokers_response, indicator='trans', currency='EUR')
            if flows is not None:
                last_flow_row = flows.iloc[0]
                flow_date = flows.index[0]
                upload_flows(flow_date, last_flow_row.to_dict(), google_sheet_flow_id, svc_sheet)

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
