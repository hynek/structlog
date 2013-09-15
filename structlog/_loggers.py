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

from functools import wraps

from structlog._compat import (
    string_types,
)
from structlog._exc import (
    DropEvent
)


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

    def __repr__(self):
        return '<PrintLogger(file={0!r})>'.format(self._file)

    def msg(self, message):
        """
        Print *message*.
        """
        print(message, file=self._file)

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


class BoundLogger(object):
    """
    Immutable, context-carrying wrapper.

    Public only for sub-classing, not intended to be instantiated by yourself.
    See :func:`~structlog.wrap_logger` and :func:`~structlog.get_logger`.
    """
    def __init__(self, logger, processors, context):
        self._logger = logger
        self._processors = processors
        self._context = context

    def __repr__(self):
        return '<BoundLogger(context={0!r}, processors={1!r})>'.format(
            self._context,
            self._processors,
        )

    def __eq__(self, other):
        try:
            if self._context == other._context:
                return True
            else:
                return False
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def bind(self, **new_values):
        """
        Return a new logger with *new_values* added to the existing ones.

        :rtype: :class:`BoundLogger`
        """
        return self.__class__(
            self._logger,
            self._processors,
            self._context.__class__(self._context, **new_values)
        )

    def unbind(self, *keys):
        """
        Return a new logger with *keys* removed from the context.

        :raises KeyError: If the key is not part of the context.

        :rtype: :class:`BoundLogger`
        """
        bl = self.bind()
        for key in keys:
            del bl._context[key]
        return bl

    def new(self, **new_values):
        """
        Clear context and binds *initial_values* using :func:`bind`.

        Only necessary with dict implementations that keep global state like
        those wrapped by :func:`structlog.threadlocal.wrap_dict` when threads
        are re-used.

        :rtype: :class:`BoundLogger`
        """
        self._context.clear()
        return self.bind(**new_values)

    def __getattr__(self, name):
        """
        If not done so yet, wrap the desired logger method & cache the result.
        """
        log_meth = getattr(self._logger, name)

        @wraps(log_meth)
        def wrapped(event=None, **kw):
            """
            Before calling actual logger method, transform the accumulated
            `context` together with the event itself using the processor
            chain.
            """
            # Explicit copy() makes sure that dicts like those from
            # _ThreadLocalDictWrapper don't get mangled by processors.
            event_dict = self._context.copy()
            event_dict.update(**kw)
            if event:
                event_dict.update(event=event)

            try:
                for proc in self._processors:
                    event_dict = proc(self._logger, name, event_dict)
            except DropEvent:
                return
            # it's not really an event_dict here anymore but a new variable
            # to indicate that seems wasteful.
            if isinstance(event_dict, string_types):
                args, kw = (event_dict,), {}
            else:
                args, kw = event_dict

            return log_meth(*args, **kw)
        setattr(self, name, wrapped)
        return wrapped
