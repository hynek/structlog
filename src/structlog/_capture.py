# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Thin module holding capture_logs.
Ended up here since there were circular references
in other likely places (``dev`` module for example).
"""

from contextlib import contextmanager

from ._config import configure, get_config
from .exceptions import DropEvent


class LogCapture(object):
    def __init__(self):
        self.entries = []

    def __call__(self, _, method_name, event_dict):
        event_dict["log_level"] = method_name
        self.entries.append(event_dict)
        raise DropEvent


@contextmanager
def capture_logs():
    """
    Context manager that appends all logging statements to its yielded list
    while it is active.

    .. versionadded:: 19.3.0
    """
    cap = LogCapture()
    old_processors = get_config()["processors"]
    try:
        configure(processors=[cap])
        yield cap.entries
    finally:
        configure(processors=old_processors)
