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

    slack_client = SlackClient(slack_api_token)
    slack_file_path = os.path.abspath(args.file)
    if not os.path.exists(slack_file_path):
        logging.warning('file {} not found: skipping'.format(slack_file_path))
        return

    json_messages = json.loads(open(slack_file_path, 'r').read())
    for json_message in json_messages:
        message_body = json_message['message_body']
        attachments = json_message['attachments']

        if message_body is None:
            logging.warning('message not specified: nothing sent')
            return

        channel = json_message['channel']
        slack_client.api_call('chat.postMessage',
                              channel='#' + channel,
                              text=message_body,
                              mrkdwn=True,
                              attachments=attachments,
                              username='InteractiveBrokers Reporting'
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
    parser.add_argument('--file', type=str, help='sends message using indicated file')

    args = parser.parse_args()
    main(args)
