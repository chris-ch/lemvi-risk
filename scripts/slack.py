import argparse
import logging
import json
import os
from slackclient import SlackClient


def main(args):
    secrets_file_name = 'secrets.json'
    secrets_file_path = os.path.abspath(secrets_file_name)

    if args.slack_api_token is not None:
        slack_api_token = args.slack_api_token

    else:
        logging.info('loading secrets file from location: {0}'.format(secrets_file_path))
        with open(secrets_file_path) as json_data:
            secrets_content = json.load(json_data)
            slack_api_token = secrets_content['slack.api.token']

    attachments = list()
    message_body = None
    if args.use_message_plain:
        message_body = args.use_message_plain

    elif args.use_message_json:
        json_message = json.loads(args.use_message_json)
        message_body = json_message['message_body']
        attachments = json_message['attachments']

    elif args.use_file_json:
        json_message = json.loads(open(args.use_file_json, 'r').read())
        message_body = json_message['message_body']
        attachments = json_message['attachments']

    slack_client = SlackClient(slack_api_token)
    slack_client.api_call('chat.postMessage',
                          channel='#' + args.channel,
                          text=message_body,
                          mrkdwn=True,
                          attachments=attachments,
                          username='Reporting - Daily NAV changes'
                          )


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    logging.getLogger('requests').setLevel(logging.WARNING)
    file_handler = logging.FileHandler('slack.log', mode='w')
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    parser = argparse.ArgumentParser(description='Sends a slack message',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                     )
    parser.add_argument('--slack-api-token', type=str, help='slack API token')
    parser.add_argument('--use-message-plain', type=str, help='sends message using indicated plain text')
    parser.add_argument('--use-message-json', type=str, help='sends message using indicated json text')
    parser.add_argument('--use-file-plain', type=str, help='sends message using indicated plain text file')
    parser.add_argument('--use-file-json', type=str, help='sends message using indicated json file')
    parser.add_argument('--channel', type=str, help='use specified channel')

    args = parser.parse_args()
    main(args)
