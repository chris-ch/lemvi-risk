import logging
import argparse
from ftplib import FTP
import os
import json

_HOST = 'ftp.interactivebrokers.com'


def retrieve_margin_report(host, ibrokers_ftp_user, ibrokers_ftp_password, retriever_func):
    logging.info('connecting to IBrokers FTP server...')
    with FTP(host=host, user=ibrokers_ftp_user, passwd=ibrokers_ftp_password) as ftp:
        ftp.cwd('outgoing')
        available_files = ftp.nlst('.')

        if len(available_files) == 0:
            return

        most_recent = sorted(available_files)[-1]
        logging.info('loading file {}'.format(most_recent))
        ftp.retrbinary('RETR {}'.format(most_recent), retriever_func(most_recent))


def data_saver(filename):
    target_file = open(filename, 'wb')
    logging.info('writing data to file {}'.format(os.path.abspath(filename)))

    def content_writer(content):
        target_file.write(content)

    return content_writer


def main():
    secrets_file_name = 'secrets.json'
    secrets_file_path = os.path.abspath(secrets_file_name)

    logging.info('loading secrets file from location: {0}'.format(secrets_file_path))
    with open(secrets_file_path) as json_data:
        secrets_content = json.load(json_data)
        ibrokers_ftp_user = secrets_content['ibrokers.ftp.user']
        ibrokers_ftp_password = secrets_content['ibrokers.ftp.password']

    host = _HOST
    retrieve_margin_report(host, ibrokers_ftp_user, ibrokers_ftp_password, retriever_func=data_saver)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler = logging.FileHandler('ibftp.log', mode='w')
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    logging.info('starting script')
    parser = argparse.ArgumentParser(description='Downloading most recent report from IBrokers FTP server',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    args = parser.parse_args()
    main()
