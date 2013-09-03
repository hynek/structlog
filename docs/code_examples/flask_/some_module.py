import logging

from structlog import BoundLogger

log = BoundLogger.wrap(logging.getLogger(__name__))


def some_function():
    # later then:
    log.error('user did something')
    # gives you:
    # request_id='ffcdc44f-b952-4b5f-95e6-0f1f3a9ee5fd' event='user did something'

