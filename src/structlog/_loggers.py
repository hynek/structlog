# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Logger wrapper and helper class.
"""

from __future__ import absolute_import, division, print_function

import sys
import threading

from pickle import PicklingError

from structlog._utils import until_not_interrupted


class PrintLoggerFactory(object):
    r"""
    Produce :class:`PrintLogger`\ s.

    To be used with :func:`structlog.configure`\ 's `logger_factory`.

    :param file file: File to print to. (default: stdout)

    Positional arguments are silently ignored.

    .. versionadded:: 0.4.0
    """

    def __init__(self, file=None):
        self._file = file

    def __call__(self, *args):
        return PrintLogger(self._file)


WRITE_LOCKS = {}


def _get_lock_for_file(file):
    global WRITE_LOCKS

    lock = WRITE_LOCKS.get(file)
    if lock is None:
        lock = threading.Lock()
        WRITE_LOCKS[file] = lock

    return lock


class PrintLogger(object):
    """
    Print events into a file.

    :param file file: File to print to. (default: stdout)

    >>> from structlog import PrintLogger
    >>> PrintLogger().msg("hello")
    hello

    Useful if you follow
    :doc:`current logging best practices <logging-best-practices>`.

    Also very useful for testing and examples since logging is finicky in
    doctests.
    """

    def __init__(self, file=None):
        self._file = file or sys.stdout
        self._write = self._file.write
        self._flush = self._file.flush

        self._lock = _get_lock_for_file(self._file)

    def __getstate__(self):
        """
        Out __getattr__ magic makes this necessary.
        """
        if self._file is sys.stdout:
            return "stdout"

        elif self._file is sys.stderr:
            return "stderr"

        raise PicklingError(
            "Only PrintLoggers to sys.stdout and sys.stderr can be pickled."
        )

    def __setstate__(self, state):
        """
        Out __getattr__ magic makes this necessary.
        """
        if state == "stdout":
            self._file = sys.stdout
        else:
            self._file = sys.stderr

        self._write = self._file.write
        self._flush = self._file.flush
        self._lock = _get_lock_for_file(self._file)

    def __repr__(self):
        return "<PrintLogger(file={0!r})>".format(self._file)

    def msg(self, message):
        """
        Print *message*.
        """
        with self._lock:
            until_not_interrupted(self._write, message + "\n")
            until_not_interrupted(self._flush)

    log = debug = info = warn = warning = msg
    fatal = failure = err = error = critical = exception = msg


class ReturnLoggerFactory(object):
    r"""
    Produce and cache :class:`ReturnLogger`\ s.

    To be used with :func:`structlog.configure`\ 's `logger_factory`.

    Positional arguments are silently ignored.

    .. versionadded:: 0.4.0
    """

    def __init__(self):
        self._logger = ReturnLogger()

    def __call__(self, *args):
        return self._logger


class ReturnLogger(object):
    """
    Return the arguments that it's called with.

    >>> from structlog import ReturnLogger
    >>> ReturnLogger().msg("hello")
    'hello'
    >>> ReturnLogger().msg("hello", when="again")
    (('hello',), {'when': 'again'})

    Useful for testing.

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
