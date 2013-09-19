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

    err = info = warning = error = critical = log = msg


class ReturnLogger(object):
    """
    Returns the string that it's called with.

    >>> from structlog import ReturnLogger
    >>> ReturnLogger().msg('hello')
    'hello'

    Useful for unit tests.
    """
    def msg(self, message):
        """
        Return *message*.
        """
        return message

    err = info = warning = error = critical = log = msg
