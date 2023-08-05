import re

import structlog

from structlog.processors import JSONRenderer, TimeStamper
from structlog.typing import EventDict, WrappedLogger


def scrub(
    logger: WrappedLogger,
    name: str,
    # ↓ annotation contradicts docs, and signature of `structlog.typing.Processor`, but
    # works as intended
    event_dict: EventDict | str,
) -> str:
    """Removes sensitive information (GitHub API tokens) from the event dict.

    Note: GH API tokens look different; this function is useless in reality.

    As these might occur at any depth, under any key, using regex is much simpler than
    any recursive approaches, looking at each key and value. It's much safer (harder to
    get wrong) and more performant (single pass, no recursion, stack cannot explode,
    ...).
    """

    if not isinstance(event_dict, str):
        # This check shouldn't be necessary when using type annotation to their full
        # potential. Used here to satisfy mypy for now.
        msg = f"Expected str, got {type(event_dict)}"
        raise TypeError(msg)

    # Clearly, `event_dict` is a misnomer by now...
    return re.sub(r"ghp_\d+", "***", event_dict)


def good() -> None:
    structlog.configure(
        processors=[
            TimeStamper(key="ts"),  # JSON -> JSON
            JSONRenderer(),  # JSON -> str
            scrub,  # str -> str
        ],
    )

    logger = structlog.get_logger()

    logger.info("hello", token="ghp_1234567890")


def woopsie() -> None:
    structlog.configure(
        processors=[
            TimeStamper(key="ts"),  # JSON -> JSON
            scrub,  # str -> str
            JSONRenderer(),  # JSON -> str
        ],
    )

    logger = structlog.get_logger()

    try:
        logger.info("hello", token="ghp_1234567890")
    except TypeError as e:
        print("This blows up, but `configure` passes type checks.")
        print(e)


good()

woopsie()
