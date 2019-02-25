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


def post_using_curl(body):
    from subprocess import check_output
    check_output(['curl', '-H', 'Content-Type: application/json', '-X', 'POST',
                  'https://tomato-bot.com/api/v1/junit/notifications', '-d', body])
    return


def post(data):
    body = json.dumps(data).encode('utf-8')
    # tomato-bot is using some new SSL features like SNI
    # Travis python version in non-python build is pretty old and canno't send SSL 1.2 requests
    # https://travis-ci.community/t/default-python-version-in-non-python-envirments/2453
    if sys.version_info < (2, 7, 10):
        logger.warning('Old python version detected, using CURL to send')
        post_using_curl(body)
        return
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
    def get_build_name():
        # https://docs.travis-ci.com/user/environment-variables/#default-environment-variables
        languages = {
            "node_js": ("TRAVIS_NODE_VERSION", "Node"),
            "python": ("TRAVIS_PYTHON_VERSION", "Python"),
            "ruby": ("TRAVIS_RUBY_VERSION", "Ruby"),
            "java": ("TRAVIS_JDK_VERSION", "Java"),
            "php": ("TRAVIS_PHP_VERSION", "PHP"),
            "dart": ("TRAVIS_DART_VERSION", "Dart"),
            "go": ("TRAVIS_GO_VERSION", "Go"),
            "haxe": ("TRAVIS_HAXE_VERSION", "Haxe"),
            "julia": ("TRAVIS_JULIA_VERSION", "Julia"),
            "erlang": ("TRAVIS_OTP_RELEASE", "Erlang"),
            "perl": ("TRAVIS_PERL_VERSION", "Perl"),
            "r": ("TRAVIS_R_VERSION", "R"),
            "rust": ("TRAVIS_RUST_VERSION", "Rust"),
            "scala": ("TRAVIS_SCALA_VERSION", "Scala"),
        }
        if environ.get('TRAVIS_JOB_NAME'):
            return environ['TRAVIS_JOB_NAME']
        if environ['TRAVIS_LANGUAGE'] in languages:
            language = languages[environ['TRAVIS_LANGUAGE']]
            return language[1] + ': ' + environ[language[0]]
        return 'Tomato'

    @staticmethod
    def parse():
        owner, repo = environ['TRAVIS_REPO_SLUG'].split('/')
        commit_hash = environ['TRAVIS_PULL_REQUEST_SHA']
        return dict(
            owner=owner,
            repo=repo,
            commit_hash=commit_hash,
            language="python",
            client="travis",
            build_name=Travis.get_build_name()
        )


class CircleCi(CI):

    @staticmethod
    def detect():
        return environ.get('CIRCLECI') == 'true'

    @staticmethod
    def parse():
        owner = environ['CIRCLE_PROJECT_USERNAME']
        repo = environ['CIRCLE_PROJECT_REPONAME']
        commit_hash = environ['CIRCLE_SHA1']
        return dict(
            owner=owner,
            repo=repo,
            commit_hash=commit_hash,
            language="python",
            client="circle",
            build_name='Tomato',
        )


class Appveyor(CI):
    @staticmethod
    def detect():
        return environ.get('APPVEYOR') == 'true'

    @staticmethod
    def parse():
        owner = environ['APPVEYOR_ACCOUNT_NAME']
        repo = environ['APPVEYOR_PROJECT_NAME']
        commit_hash = environ['APPVEYOR_PULL_REQUEST_HEAD_COMMIT']
        return dict(
            owner=owner,
            repo=repo,
            commit_hash=commit_hash,
            language="python",
            client="appveyor",
            build_name='Tomato',
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
    logging.basicConfig()
    if len(sys.argv) == 1:
        logger.warning('\nUsage: %s xml_files...' % (sys.argv[0]))
        exit(1)
    send_payload(sys.argv[1:], client='cli')


if __name__ == '__main__':
    cli()
