# coding=utf-8
import os
import sys

try:
    from HTMLParser import HTMLParser
except:
    from html.parser import HTMLParser

import requests

sess = requests.session()

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        output = ''
        for line in self.fed:
            if (line.strip()):
                output += '\n{0}'.format(line.encode('utf-8'))
        return output


POST_URL = 'https://slack.com/api/chat.postMessage'

ignore = os.environ.get('IGNORE_WORDS')
IGNORE_WORDS = ignore.split(',') if ignore else []
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', '#general')

try:
    SLACK_API_TOKEN = os.environ['SLACK_API_TOKEN']
except KeyError as error:
    sys.stderr.write('Please set the environment variable {0}'.format(error))
    sys.exit(1)

INITIAL_MESSAGE = """\
Hi! There's a few menus for lunch you should take a \
look at:

"""


def format_restaurant(restaurant, menu_lines):
    lines = []

    for course in menu_lines:
        line = '*[{0}]* <{1}>'.format(
            restaurant, course)
        lines.append(line)

    return lines


def fetch_url(url):
    try:
        response = sess.get(url, headers={'Accept-Language': 'en-EN'}, verify=False)
    except (requests.exceptions.MissingSchema,
            requests.exceptions.InvalidSchema):
        print("*FAILED*: ", url)
        return None

    if response.headers['content-type'].startswith('text/html'):
        return response.content.decode('utf-8')
    return None


def fetch_escola():

    content = fetch_url('http://dinsescola.org/restaurants/')

    start_i = content.find('<h2>')
    end_i = content.find('</section>', start_i)
    return content[start_i:end_i]

def fetch_entrechinos():
    content = fetch_url('https://m.facebook.com/SaborMudejar/')
    menu_mudejar_i = content.find(u'MENÚ')
    end_menu_mudejar_i = content.find('Public', menu_mudejar_i)
    return content[menu_mudejar_i:end_menu_mudejar_i]


def fetch_restaurants():
    """
    Returns a formatted string list
    """
    # todo crawl escola, entrechinos
    stripper = MLStripper()
    lines = []

    stripper.feed(fetch_escola() + '\n\n')
    stripper.feed("*****************************************")
    #stripper.feed(fetch_entrechinos())
    lines.append(stripper.get_data())
    return lines


def send_to_slack(text):
    payload = {
        'token': SLACK_API_TOKEN,
        'channel': SLACK_CHANNEL,
        'username': 'Restaurant Reminder',
        'icon_emoji': ':sushi:',
        'text': text
    }

    response = requests.post(POST_URL, data=payload, verify=False)
    answer = response.json()
    if not answer['ok']:
        raise Exception(answer['error'])


def cli():
    lines = fetch_restaurants()
    if lines:
        text = INITIAL_MESSAGE + '\n'.join(lines)
        send_to_slack(text)


if __name__ == '__main__':
    cli()

