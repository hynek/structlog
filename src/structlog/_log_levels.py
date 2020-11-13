"""
Extracted log level data used by both stdlib and native log level filters.
"""

# Adapted from the stdlib
CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

_NAME_TO_LEVEL = {
    "critical": CRITICAL,
    "exception": ERROR,
    "error": ERROR,
    "warn": WARNING,
    "warning": WARNING,
    "info": INFO,
    "debug": DEBUG,
    "notset": NOTSET,
}

_LEVEL_TO_NAME = {
    v: k
    for k, v in _NAME_TO_LEVEL.items()
    if k not in ("warn", "exception", "notset")
}
