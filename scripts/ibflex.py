import argparse
import logging
import json
import os
from string import Template
from time import sleep
from xml.etree import ElementTree
import requests

from ibrokersflex import parse_flex_accounts

_FLEX_QUERY_ID = '251102'
_FLEX_QUERY_SERVER = 'gdcdyn.interactivebrokers.com'
_FLEX_QUERY_PATH = 'Universal/servlet/FlexStatementService.SendRequest'
_FLEX_QUERY_URL_PATTERN = Template('https://$server/$path?t=$token&q=$query_id&v=3')


def serialize_message_unique(message_body, attachments):
    return json.dumps({'message_body': message_body, 'attachments': attachments})


def serialize_accounts(accounts):
    items = list()
    for account_id in accounts:
        if account_id.endswith('F'):
            # paired UK accounts are processed together with main US LLC account
            continue

        account_data = accounts[account_id]
        uk_account_id = account_id + 'F'
        if uk_account_id in accounts:
            account_data['nav_end'] += accounts[uk_account_id]['nav_end']
            account_data['nav_change'] += accounts[uk_account_id]['nav_change']

        channel = 'reporting-{}'.format(account_data['account_id'].lower())
        content = '{0}: {1:,d} ({2:,d})'.format(account_data['as_of_date'], account_data['nav_end'], account_data['nav_change'])
        items.append({'channel': channel, 'message_body': content, 'attachments': []})

    return json.dumps(items)


def create_flex_request_step_1(token):
    flex_params = {
        'server': _FLEX_QUERY_SERVER,
        'path': _FLEX_QUERY_PATH,
        'token': token,
        'query_id': _FLEX_QUERY_ID,
    }
    return _FLEX_QUERY_URL_PATTERN.safe_substitute(flex_params)


def create_flex_request_step_2(url, reference_code, token):
    step_2_pattern = Template('$url?q=$reference_code&t=$token&v=3')
    params = {'url': url, 'reference_code': reference_code, 'token': token}
    return step_2_pattern.safe_substitute(params)


def flex_request(token):
    """
    Requesting IBrokers Flex data.
    :param token: 
    :return: dict() of accounts data using account id as key
    """
    request_step_1 = create_flex_request_step_1(token)
    logging.info('requesting: "{0}"'.format(request_step_1))
    response_1 = requests.get(request_step_1)
    tree_1 = ElementTree.fromstring(response_1.content)
    error_code = tree_1.findtext('ErrorCode')
    if error_code:
        error_message = tree_1.findtext('ErrorMessage')
        logging.error('failed to access IBrokers Flex service: "{0}" (code {1})'.format(error_message, error_code))
        raise Exception(error_message, error_code)

    reference_code = tree_1.findtext('ReferenceCode')
    url = tree_1.findtext('Url')
    logging.info('reference code: {0}'.format(reference_code))
    logging.info('url: {0}'.format(url))
    request_step_2 = create_flex_request_step_2(url, reference_code, token)
    logging.info('requesting url "{0}"'.format(request_step_2))
    error_code = '1019'  # goes through the loop at least once
    attempt = 1
    attempt_total = 6
    response_2 = None
    while error_code == '1019' and attempt <= attempt_total:
        params = {'attempt': attempt, 'total': attempt_total}
        logging.info(Template('requesting attempt $attempt / $total').safe_substitute(params))
        response_2 = requests.get(request_step_2)
        tree_2 = ElementTree.fromstring(response_2.content)
        error_code = tree_2.findtext('ErrorCode')
        sleep(5)
        attempt += 1

    return response_2.text


def main(args):
    if args.use_ibrokers_response:
        with open(args.use_ibrokers_response, 'r') as ibrokers_response_file:
            ibrokers_response = ibrokers_response_file.read()

    else:
        secrets_file_name = 'secrets.json'
        secrets_file_path = os.path.abspath(secrets_file_name)

        if args.ibrokers_flex_token is not None:
            ibrokers_flex_token = args.ibrokers_flex_token

        else:
            with open(secrets_file_path) as json_data:
                secrets_content = json.load(json_data)
                ibrokers_flex_token = secrets_content['ibrokers.flex.token']

        ibrokers_response = flex_request(ibrokers_flex_token)
        os.makedirs(args.output_path, exist_ok=True)
        if args.save_ibrokers_data:
            target_ibrokers_file = os.path.abspath(os.sep.join([args.output_path, args.save_ibrokers_data]))
            with open(target_ibrokers_file, 'w') as ibrokers_data:
                logging.info('saving InteractiveBorkers response to file {}'.format(target_ibrokers_file))
                ibrokers_data.write(ibrokers_response)

    accounts = parse_flex_accounts(ibrokers_response)
    total_cash, total_nav, attachments = create_nav_summary(accounts)
    message_body = '\n'.join(['*Daily reporting - NAV changes*', 'NAV: {0:,d}'.format(int(total_nav)),
                              'Cash: {0:,d}'.format(int(total_cash))])

    output_summary = serialize_message_unique(message_body, attachments)
    if args.file_summary:
        target_file = os.sep.join([args.output_path, args.file_summary])
        logging.info('saving data to {}'.format(os.path.abspath(target_file)))
        with open(target_file, 'w') as file_summary:
            file_summary.write(output_summary)

    else:
        print(output_summary)

    output_accounts = serialize_accounts(accounts)
    if args.file_accounts:
        target_file = os.sep.join([args.output_path, args.file_accounts])
        logging.info('saving data to {}'.format(os.path.abspath(target_file)))
        with open(target_file, 'w') as file_accounts:
            file_accounts.write(output_accounts)

    else:
        print(output_accounts)


def create_nav_summary(accounts):
    attachments = list()
    total_cash = 0.
    total_nav = 0.

    for account_id in accounts:
        if account_id.endswith('F'):
            # paired UK accounts are processed together with main US LLC account
            continue

        account_data = accounts[account_id]
        uk_account_id = account_id + 'F'
        if uk_account_id in accounts:
            account_data['nav_start'] += accounts[uk_account_id]['nav_start']
            account_data['nav_end'] += accounts[uk_account_id]['nav_end']
            account_data['nav_change'] += accounts[uk_account_id]['nav_change']
            account_data['cash'] += accounts[uk_account_id]['cash']

        attachment_description = '{} ({}) - {}'.format(
            account_data['account_id'],
            account_data['account_alias'],
            account_data['currency']
        )

        attachment = {'color': '#F35A00', 'text': attachment_description}
        account_fields = [
            {'title': 'NAV change ({0}, from {1:,d} to {2:,d})'.format(account_data['as_of_date'],
                                                                       account_data['nav_start'],
                                                                       account_data['nav_end']),
             'value': '{0:,d}'.format(account_data['nav_change']), 'short': False}
        ]
        attachment['fields'] = account_fields
        attachments.append(attachment)

        total_cash += accounts[account_id]['cash']
        total_nav += accounts[account_id]['nav_end']

    return total_cash, total_nav, attachments

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    logging.getLogger('requests').setLevel(logging.WARNING)
    file_handler = logging.FileHandler('ibflex.log', mode='w')
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    parser = argparse.ArgumentParser(description='Daily NAV data retrieval.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                     )
    parser.add_argument('--ibrokers-flex-token', type=str, help='InteractiveBrokers Flex token')
    parser.add_argument('--use-ibrokers-response', type=str, help='use specified file as InteractiveBrokers response')
    parser.add_argument('--output-path', type=str, help='output path', default='.')
    parser.add_argument('--file-summary', type=str, help='output summary file name')
    parser.add_argument('--file-accounts', type=str, help='output by account file name')
    parser.add_argument('--save-ibrokers-data', type=str, help='keep InteractiveBrokers response data')

    args = parser.parse_args()
    main(args)
