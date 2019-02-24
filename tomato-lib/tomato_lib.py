import json
import logging
import sys
from os import environ

try:
    from urllib2 import urlopen, Request
except ImportError:
    from urllib.request import urlopen, Request

logger = logging.getLogger("tomato")
URL = environ.get('TOMATO_URL', 'https://tomato-bot.com') + '/api/v1/junit/notifications'


def post(data):
    body = json.dumps(data).encode('utf-8')
    logger.warning(body)
    logger.warning(json.dumps(dict(environ)))
    clen = len(body)
    req = Request(URL, body, {'Content-Type': 'application/json', 'Content-Length': clen})
    f = urlopen(req)
    response = f.read()
    f.close()
    logger.warning(response)


class CI(object):
    @staticmethod
    def detect():
        raise NotImplementedError

    @staticmethod
    def parse():
        raise NotImplementedError


class Travis(CI):
    @staticmethod
    def detect():
        return environ.get('TRAVIS') == 'true' \
            and environ.get('TRAVIS_PULL_REQUEST') != 'false' \
            and environ['TRAVIS_EVENT_TYPE'] == 'pull_request' \
            and environ.get('TRAVIS_ALLOW_FAILURE') != 'true'

    @staticmethod
    def parse():
        owner, repo = environ['TRAVIS_REPO_SLUG'].split('/')
        issue_id = environ['TRAVIS_PULL_REQUEST']
        commit_hash = environ['TRAVIS_PULL_REQUEST_SHA']
        return dict(
            owner=owner,
            repo=repo,
            issue_id=issue_id,
            commit_hash=commit_hash,
            language="python",
            client="travis",
        )


class CircleCi(CI):

    @staticmethod
    def detect():
        return environ.get('CIRCLECI') == 'true'

    @staticmethod
    def parse():
        owner = environ['CIRCLE_PROJECT_USERNAME']
        repo = environ['CIRCLE_PROJECT_REPONAME']
        issue_id = environ['CIRCLE_PULL_REQUEST'].rsplit('/')[-1]
        commit_hash = environ['CIRCLE_SHA1']
        return dict(
            owner=owner,
            repo=repo,
            issue_id=issue_id,
            commit_hash=commit_hash,
            language="python",
            client="circle",
        )


class Appveyor(CI):
    @staticmethod
    def detect():
        return environ.get('APPVEYOR') == 'true'

    @staticmethod
    def parse():
        owner = environ['APPVEYOR_ACCOUNT_NAME']
        repo = environ['APPVEYOR_PROJECT_NAME']
        issue_id = environ['APPVEYOR_PULL_REQUEST_NUMBER']
        commit_hash = environ['APPVEYOR_PULL_REQUEST_HEAD_COMMIT']
        return dict(
            owner=owner,
            repo=repo,
            issue_id=issue_id,
            commit_hash=commit_hash,
            language="python",
            client="appveyor",
        )


def send_payload(xmls, client):
    for ci in [CircleCi, Travis, Appveyor]:
        if not ci.detect():
            continue
        data = {"xmls": [open(xml).read() for xml in xmls]}
        data.update(ci.parse())
        data['client'] = client + "/" + data['client']
        logger.debug("Detected CI environment - %s", data['client'])
        post(data)
        return data


def cli():
    if len(sys.argv) == 1:
        print('Usage: %s xml_files...' % (sys.argv[0]))
        exit(1)
    send_payload(sys.argv[1:], client='cli')


if __name__ == '__main__':
    cli()
