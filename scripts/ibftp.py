import logging
import argparse
from ftplib import FTP
import os
import json
from io import StringIO

from ibrokersmargin import parse_csv_margin_data, get_margin_data

_HOST = 'ftp.interactivebrokers.com'


def retrieve_margin_report(host, ibrokers_ftp_user, ibrokers_ftp_password, retriever_func):
    logging.info('connecting to IBrokers FTP server...')
    with FTP(host=host, user=ibrokers_ftp_user, passwd=ibrokers_ftp_password) as ftp:
        ftp.cwd('outgoing')
        available_files = ftp.nlst('.')

        if len(available_files) == 0:
            return

        most_recent_file = sorted(available_files)[-1]
        ftp.voidcmd('TYPE I')
        if ftp.size(most_recent_file) == 0:
            most_recent_file = sorted(available_files)[-2]

        logging.info('loading file {}'.format(most_recent_file))
        ftp.retrbinary('RETR {}'.format(most_recent_file), retriever_func(most_recent_file))


def retrieve_ibrokers_data(ibrokers_data, keep_ibrokers, output_path):
    def data_saver(filename):
        if keep_ibrokers:
            target_filename = os.sep.join([output_path, filename])
            logging.info('writing data to file {}'.format(os.path.abspath(target_filename)))
            target_file = open(target_filename, 'w')

            def content_writer_both(content):
                target_file.write(content.decode())
                ibrokers_data.write(content.decode())

            content_writer = content_writer_both

        else:
            def content_writer_memory(content):
                ibrokers_data.write(content)

            content_writer = content_writer_memory

        return content_writer

    return data_saver


def main(args):
    secrets_file_name = 'secrets.json'
    secrets_file_path = os.path.abspath(secrets_file_name)

    logging.info('loading secrets file from location: {0}'.format(secrets_file_path))
    with open(secrets_file_path) as json_data:
        secrets_content = json.load(json_data)
        ibrokers_ftp_user = secrets_content['ibrokers.ftp.user']
        ibrokers_ftp_password = secrets_content['ibrokers.ftp.password']
        host = _HOST
        os.makedirs(args.output_path, exist_ok=True)
        target_file = os.sep.join([args.output_path, args.output_file])
        logging.info('saving data to {}'.format(os.path.abspath(target_file)))
        ibrokers_data = StringIO()
        retrieve_margin_report(host, ibrokers_ftp_user, ibrokers_ftp_password, retriever_func=retrieve_ibrokers_data(ibrokers_data, args.keep_raw_ibrokers, args.output_path))
        ibrokers_data.seek(0)
        ib_margin_data = parse_csv_margin_data(ibrokers_data)
        result = get_margin_data(ib_margin_data)
        output_data = {
            'as_of_date': result['as_of_date'],
            'currency': result['base_currency'],
            'nav': result['net_liquidation_value'],
            'cash': result['cash_value'],
            'initial_margin': result['initial_margin_requirement'],
            'maintenance_margin': result['maintenance_margin_requirement'],
        }
        lines = ["*Daily reporting - Margin {currency} {as_of_date}*",
                 "NAV: {nav}","Cash: {cash}",
                 "Initial Margin: {initial_margin}",
                 "Maintenance Margin: {maintenance_margin}"
                 ]
        output_content = '\n'.join(lines).format(**output_data)

        os.makedirs(args.output_path, exist_ok=True)
        if args.output_file:
            target_file = os.sep.join([args.output_path, args.output_file])
            logging.info('saving data to {}'.format(os.path.abspath(target_file)))
            with open(target_file, 'w') as output_file:
                output_file.write(output_content)

        else:
            print(output_content)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler = logging.FileHandler('ibftp.log', mode='w')
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    logging.info('starting script')
    parser = argparse.ArgumentParser(description='Downloading most recent report from IBrokers FTP server',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--keep-raw-ibrokers', action='store_true', help='keep raw IBrokers file')
    parser.add_argument('--output-path', type=str, help='output path', default='.')
    parser.add_argument('--output-file', type=str, help='output file name', default='slack-margin.txt')

    args = parser.parse_args()
    main(args)
