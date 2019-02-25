from contextlib import contextmanager

from tomato_lib import Travis
from os import environ


@contextmanager
def set_env(key, value):
    old = environ.get(key)
    environ[key] = value
    yield
    if old is None:
        environ.pop(key)
    else:
        environ[key] = old


def test_build_name_has_job_name():
    build_name = 'build_name'
    with set_env('TRAVIS_JOB_NAME', build_name):
        assert Travis.get_build_name() == build_name


def test_build_infer_job_name():
    with set_env('TRAVIS_LANGUAGE', 'python'), set_env('TRAVIS_PYTHON_VERSION', '2.7'):
        assert Travis.get_build_name() == 'Python: 2.7'


def test_build_name_default_job_name():
    with set_env('TRAVIS_LANGUAGE', 'nolang'):
        assert Travis.get_build_name() == 'Tomato'
