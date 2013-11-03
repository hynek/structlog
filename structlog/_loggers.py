# Copyright 2013 Hynek Schlawack
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Logger wrapper and helper class.
"""

from __future__ import absolute_import, division, print_function

import sys

from structlog._utils import until_not_interrupted


class PrintLoggerFactory(object):
    """
    Produces :class:`PrintLogger`\ s.

    To be used with :func:`structlog.configure`\ 's `logger_factory`.

    :param file file: File to print to. (default: stdout)

    Positional arguments are silently ignored.

    .. versionadded:: 0.4.0
    """
    def __init__(self, file=None):
        self._file = file

    def __call__(self, *args):
        return PrintLogger(self._file)


class PrintLogger(object):
    """
    Prints events into a file.

    :param file file: File to print to. (default: stdout)

    >>> from structlog import PrintLogger
    >>> PrintLogger().msg('hello')
    hello

    Useful if you just capture your stdout with tools like `runit
    <http://smarden.org/runit/>`_ or if you `forward your stderr to syslog
    <http://hynek.me/articles/taking-some-pain-out-of-python-logging/>`_.

    Also very useful for testing and examples since logging is sometimes
    finicky in doctests.
    """
    def __init__(self, file=None):
        self._file = file or sys.stdout
        self._write = self._file.write
        self._flush = self._file.flush

    def __repr__(self):
        return '<PrintLogger(file={0!r})>'.format(self._file)

    def msg(self, message):
        """
        Print *message*.
        """
        until_not_interrupted(self._write, message + '\n')
        until_not_interrupted(self._flush)

    err = debug = info = warning = error = critical = log = msg


class ReturnLoggerFactory(object):
    """
    Produces and caches :class:`ReturnLogger`\ s.

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
    Returns the string that it's called with.

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

    err = debug = info = warning = error = critical = log = msg
