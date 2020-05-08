# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Helpers to test your application's logging behavior.

.. versionadded:: 20.1.0

See :doc:`testing`.
"""

from contextlib import contextmanager

from ._config import configure, get_config
from .exceptions import DropEvent


__all__ = ["LogCapture", "capture_logs"]


class LogCapture:
    """
    Class for capturing log messages in its entries list.
    Generally you should use `structlog.testing.capture_logs`,
    but you can use this class if you want to capture logs with other patterns.

    .. versionadded:: 20.1.0
    """

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
    while it is active. Disables all configured processors for the duration
    of the context manager.

    Attention: this is **not** thread-safe!

    .. versionadded:: 20.1.0
    """
    cap = LogCapture()
    old_processors = get_config()["processors"]
    try:
        configure(processors=[cap])
        yield cap.entries
    finally:
        configure(processors=old_processors)


class ReturnLoggerFactory:
    r"""
    Produce and cache `ReturnLogger`\ s.

    To be used with `structlog.configure`\ 's *logger_factory*.

    Positional arguments are silently ignored.

    .. versionadded:: 0.4.0
    """

    def __init__(self):
        self._logger = ReturnLogger()

    def __call__(self, *args):
        return self._logger


class ReturnLogger:
    """
    Return the arguments that it's called with.

    >>> from structlog import ReturnLogger
    >>> ReturnLogger().msg("hello")
    'hello'
    >>> ReturnLogger().msg("hello", when="again")
    (('hello',), {'when': 'again'})

    .. versionchanged:: 0.3.0
        Allow for arbitrary arguments and keyword arguments to be passed in.
    """

    def msg(self, *args, **kw):
        """
        Return tuple of ``args, kw`` or just ``args[0]`` if only one arg passed
        """
        # Slightly convoluted for backwards compatibility.
        if len(args) == 1 and not kw:
            return args[0]
        else:
            return args, kw

    log = debug = info = warn = warning = msg
    fatal = failure = err = error = critical = exception = msg
