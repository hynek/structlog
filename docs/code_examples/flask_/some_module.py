from structlog import get_logger


logger = get_logger()


def some_function():
    # ...
    logger.error("user did something", something="shot_in_foot")
    # ...
