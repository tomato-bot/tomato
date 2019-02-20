import json
import logging
import tempfile
from os import environ, remove

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
        return environ.get('TRAVIS') == 'true'

    @staticmethod
    def parse():
        owner, repo = environ['TRAVIS_REPO_SLUG'].split('/')
        issue_id = environ['TRAVIS_PULL_REQUEST']
        return dict(
            owner=owner,
            repo=repo,
            issue_id=issue_id,
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
        return dict(
            owner=owner,
            repo=repo,
            issue_id=issue_id,
            language="python",
            client="pytest/circle",
        )


state = {
    "created": False,
    "path": None,
}


def pytest_load_initial_conftests(args):
    if '--junit-xml' in args or '--junitxml' in args:
        return
    fp = tempfile.NamedTemporaryFile(delete=False)
    logger.info('Creating tomato.xml file due to missing --junit-xml flag')
    state["created"] = True
    state["path"] = fp.name
    fp.close()
    args[:] = ["--junit-xml", state["path"]] + args


def pytest_sessionfinish(session):
    if session.config.option.xmlpath is None:
        logger.warning("Tomato plugin disabled due to missing --junit-xml flag")
        return
    for ci in [CircleCi, Travis]:
        if not ci.detect():
            continue
        data = {"xml": open(session.config.option.xmlpath).read()}
        data.update(ci.parse())
        logger.debug("Detected CI environment - %s", data['client'])
        post(data)
        if state["created"] is True:
            remove(state["path"])
        return
