# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Logger wrapper and helper class.
"""

from __future__ import absolute_import, division, print_function

import sys
import threading

from structlog._utils import until_not_interrupted


class PrintLoggerFactory(object):
    """
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


class PrintLogger(object):
    """
    Print events into a file.

    :param file file: File to print to. (default: stdout)

    >>> from structlog import PrintLogger
    >>> PrintLogger().msg('hello')
    hello

    Useful if you just capture your stdout with tools like `runit
    <http://smarden.org/runit/>`_ or if you `forward your stderr to syslog
    <https://hynek.me/articles/taking-some-pain-out-of-python-logging/>`_.

    Also very useful for testing and examples since logging is finicky in
    doctests.
    """
    def __init__(self, file=None):
        self._file = file or sys.stdout
        self._write = self._file.write
        self._flush = self._file.flush

        lock = WRITE_LOCKS.get(self._file)
        if lock is None:
            lock = threading.Lock()
            WRITE_LOCKS[self._file] = lock
        self._lock = lock

    def __repr__(self):
        return '<PrintLogger(file={0!r})>'.format(self._file)

    def msg(self, message):
        """
        Print *message*.
        """
        with self._lock:
            until_not_interrupted(self._write, message + '\n')
            until_not_interrupted(self._flush)

    log = debug = info = warn = warning = msg
    failure = err = error = critical = exception = msg


class ReturnLoggerFactory(object):
    """
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
    >>> ReturnLogger().msg('hello')
    'hello'
    >>> ReturnLogger().msg('hello', when='again')
    (('hello',), {'when': 'again'})

    Useful for unit tests.

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
    failure = err = error = critical = exception = msg
