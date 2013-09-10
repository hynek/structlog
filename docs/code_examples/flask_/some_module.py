from structlog import get_logger

logger = get_logger()


def some_function():
    # later then:
    logger.error('user did something', something='shot_in_foot')
    # gives you:
    # request_id='ffcdc44f-b952-4b5f-95e6-0f1f3a9ee5fd' something='shot_in_foot' event='user did something'

