import json
import logging
import sys
from os import environ

try:
    from urllib2 import urlopen, Request
except ImportError:
    from urllib.request import urlopen, Request

logger = logging.getLogger("tomato")
URL = 'https://tomato-bot.com/api/v1/junit/notifications'


def post(data):
    body = json.dumps(data).encode('utf-8')
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
        return environ.get('TRAVIS') == 'true' and environ.get('TRAVIS_PULL_REQUEST') != 'false'

    @staticmethod
    def parse():
        owner, repo = environ['TRAVIS_REPO_SLUG'].split('/')
        issue_id = environ['TRAVIS_PULL_REQUEST']
        commit_hash = environ['TRAVIS_COMMIT']
        return dict(
            owner=owner,
            repo=repo,
            issue_id=issue_id,
            commit_hash=commit_hash,
            language="python",
            client="pytest/travis",
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
            client="pytest/circle",
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
            client="pytest/appveyor",
        )


def send_payload(xml_path):
    for ci in [CircleCi, Travis, Appveyor]:
        if not ci.detect():
            continue
        data = {"xml": open(xml_path).read()}
        data.update(ci.parse())
        logger.debug("Detected CI environment - %s", data['client'])
        post(data)
        return data


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('Usage: %s xml_file' % (sys.argv[0]))
        exit(1)
    data = send_payload(sys.argv[1])
    print(data)
    print(environ)
