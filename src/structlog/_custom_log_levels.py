# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from ._log_levels import LEVEL_TO_NAME, NAME_TO_LEVEL
from ._native import (
    add_new_custom_level_filtering,
    remove_custom_level_filtering,
)
from ._output import add_new_custom_level_method, remove_custom_level_method


CUSTOM_LOG_LEVEL_NAMES: set[str] = set()
CUSTOM_LOG_LEVELS: set[int] = set()

# Forbid use of well-known names that would cause confusion.
FORBIDDEN_LEVEL_NAMES: frozenset[str] = frozenset(
    (
        # expected logger methods, sync and async variants
        "critical",
        "acritical",
        "debug",
        "adebug",
        "err",
        "aerr",
        "error",
        "aerror",
        "exception",
        "aexception",
        "failure",
        "afailure",
        "fatal",
        "afatal",
        "info",
        "ainfo",
        "log",
        "alog",
        "warn",
        "awarn",
        "warning",
        "awarning",
        "msg",
        "amsg",
        # NOTSET is a special 0-valued level, but not a method name
        "notset",
    )
)


def register_log_level(name: str, level: int, /) -> None:
    """Register a custom log level for use with structlog.

    Loggers will be automatically enabled for use with this log level, with a method
    named by the given level name.

    The log level will not be registered in the standard library `logging` module.

    Both the name and level must be distinct from names and levels already in use.
    Names and levels which are already used will be rejected with an error, as will
    level names which are not valid identifiers and level names which match structlog
    method names.

    Args:
        name: The name of the log level.

        level:
            The numeric value of the log level as an integer.
            This determines level-based filtering behavior.
    """
    if not name.isidentifier():
        msg = f"Log level names must be valid identifiers. Got {name!r}"
        raise ValueError(msg)
    if name.startswith("_"):
        msg = f"Log level names can't start with '_'. Got {name!r}"
        raise ValueError(msg)
    if name in FORBIDDEN_LEVEL_NAMES or name in NAME_TO_LEVEL:
        msg = (
            "register_log_level() cannot be used with names which are "
            f"already in use. Got: {name!r}"
        )
        raise ValueError(msg)
    if level in LEVEL_TO_NAME:
        msg = (
            "register_log_level() cannot be used with levels which are "
            f"already in use. Got {level!r}, "
            f"which maps to {LEVEL_TO_NAME[level]!r}"
        )
        raise ValueError(msg)

    CUSTOM_LOG_LEVEL_NAMES.add(name)
    CUSTOM_LOG_LEVELS.add(level)

    NAME_TO_LEVEL[name] = level
    LEVEL_TO_NAME[level] = name
    add_new_custom_level_method(name)
    add_new_custom_level_filtering(name)


def reset_log_levels() -> None:
    """
    Reset all custom log levels and log level names.
    """
    while CUSTOM_LOG_LEVEL_NAMES:
        name = CUSTOM_LOG_LEVEL_NAMES.pop()
        remove_custom_level_filtering(name)
        remove_custom_level_method(name)
        del NAME_TO_LEVEL[name]

    while CUSTOM_LOG_LEVELS:
        level = CUSTOM_LOG_LEVELS.pop()
        del LEVEL_TO_NAME[level]
