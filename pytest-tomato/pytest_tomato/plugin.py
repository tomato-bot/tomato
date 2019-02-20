import logging
import tempfile
from os import remove

from tomato_lib import send_payload

logger = logging.getLogger("tomato")


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
    send_payload(session.config.option.xmlpath)
    if state["created"] is True:
        remove(state["path"])
    return
