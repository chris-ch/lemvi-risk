import os
from slackclient import SlackClient
import json

def main(args):
    slack_token = os.environ['SLACK_API_TOKEN']
    sc = SlackClient(slack_token)
    sc.api_call('chat.postMessage', channel='#python', text='Hello from Python! :tada:')

    with open('strings.json') as json_data:
        d = json.load(json_data)
        print(d)

if __name__ == '__main__':
    args = None
    main(args)

