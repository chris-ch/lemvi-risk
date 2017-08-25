import argparse
import json
import logging
import os
from datetime import datetime

import tenacity

import gservices
from risklimits import extract_navs, compute_high_watermark, extract_flows


def from_excel_datetime(excel_date):
    return datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(excel_date) - 2)


def from_excel_date(excel_date):
    return from_excel_datetime(excel_date).date()


@tenacity.retry(wait=tenacity.wait_fixed(100), stop=tenacity.stop_after_attempt(5))
def main(args):
    full_config_path = os.path.abspath(args.config)
    logging.info('using config file "{}"'.format(full_config_path))
    with open(full_config_path, 'r') as config_file:
        config = json.load(config_file)

    secrets_file_path = os.path.abspath(args.file_secret)
    logging.info('using secrets file "{}"'.format(secrets_file_path))
    with open(secrets_file_path) as json_data:
        secrets_content = json.load(json_data)
        google_credential = secrets_content['google.credential']
        authorized_http, credentials = gservices.authorize_services(google_credential)
        svc_sheet = gservices.create_service_sheets(credentials)
        google_sheet_flow_id = config['google.sheet.flows.id']
        workbook_flows = svc_sheet.open_by_key(google_sheet_flow_id)
        flows = workbook_flows.worksheet_by_title('Flows EUR').get_all_records()
        google_sheet_nav_id = config['google.sheet.navs.id']
        workbook_navs = svc_sheet.open_by_key(google_sheet_nav_id)
        navs = dict()
        for tab in workbook_navs.worksheets():
            navs[tab.title] = tab.get_all_records()

        hwms, drawdowns = compute_high_watermark(extract_flows(flows), extract_navs(navs))
        google_sheet_risk_limits_id = config['google.sheet.risk_limits.id']
        workbook_risk_limits = svc_sheet.open_by_key(google_sheet_risk_limits_id)
        sheet_hwm = workbook_risk_limits.worksheet_by_title('Adjusted High Watermarks')
        sheet_drawdowns = workbook_risk_limits.worksheet_by_title('Drawdowns')
        sheet_limits = workbook_risk_limits.worksheet_by_title('Risk Limits')
        header_hwms = sheet_hwm.get_row(1, returnas='matrix')
        header_drawdowns = sheet_drawdowns.get_row(1, returnas='matrix')
        last_hwm_update = datetime.strptime(sheet_hwm.cell('A2').value, '%Y-%m-%d').date()
        last_drawdown_update = datetime.strptime(sheet_drawdowns.cell('A2').value, '%Y-%m-%d').date()

        last_hwms = hwms[hwms.index > last_hwm_update].sort_index(ascending=False)
        for as_of_date, row in last_hwms.iterrows():
            row_data = [as_of_date.strftime('%Y-%m-%d')]
            for account_id in header_hwms[1:]:
                value = row.to_dict()[account_id]
                row_data.append(float(value))

            sheet_hwm.insert_rows(row=1, number=1, values=[row_data])

        last_drawdowns = drawdowns[drawdowns.index > last_drawdown_update].sort_index(ascending=False)
        for as_of_date, row in last_drawdowns.iterrows():
            row_data = [as_of_date.strftime('%Y-%m-%d')]
            for account_id in header_drawdowns[1:]:
                value = row.to_dict()[account_id]
                row_data.append(float(value))

            sheet_drawdowns.insert_rows(row=1, number=1, values=[row_data])


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
