from structlog.stdlib import get_logger

logger = get_logger()


def some_function():
    # later then:
    logger.error('user did something')
    # gives you:
    # request_id='ffcdc44f-b952-4b5f-95e6-0f1f3a9ee5fd' event='user did something'

