# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fine-grained log-level filtering recipe.

Used from docs/recipes.md via literalinclude.
"""

import structlog


logger = structlog.get_logger()


def f():
    logger.info("f called")


def g():
    logger.info("g called")


def filter_f(_, __, event_dict):
    if event_dict.get("func_name") == "f":
        raise structlog.DropEvent

    return event_dict


structlog.configure(
    processors=[
        structlog.processors.CallsiteParameterAdder(
            [structlog.processors.CallsiteParameter.FUNC_NAME]
        ),
        filter_f,  # <-- your processor!
        structlog.processors.KeyValueRenderer(),
    ]
)

f()
g()
