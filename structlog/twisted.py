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
Processors and tools specific to the `Twisted <http://twistedmatrix.com/>`_
networking engine.
"""

from __future__ import absolute_import, division, print_function

import sys

from twisted.python.failure import Failure

from structlog._compat import string_types
from structlog.processors import (
    KeyValueRenderer,
    # can't import processors module because of circular imports
    JSONRenderer as _JSONRenderer
)


class LoggerFactory(object):
    """
    Build a Twisted logger when an *instance* is called.

    >>> from structlog import configure
    >>> from structlog.twisted import LoggerFactory
    >>> configure(logger_factory=LoggerFactory())
    """
    def __call__(self, name=None):
        """
        :rvalue: A new Twisted logger.
        """
        from twisted.python import log
        return log


_FAIL_TYPES = (BaseException, Failure)


def _extractStuffAndWhy(eventDict):
    """
    Removes all possible *_why*s and *_stuff*s, analyzes exc_info and returns
    a tuple of `(_stuff, _why, eventDict)`.

    **Modifies** *eventDict*!
    """
    _stuff = eventDict.pop('_stuff', None)
    _why = eventDict.pop('_why', None)
    event = eventDict.pop('event', None)
    if (
        isinstance(_stuff, _FAIL_TYPES) and
        isinstance(event, _FAIL_TYPES)
    ):
        raise ValueError('Both _stuff and event contain an Exception/Failure.')
    # `log.err('event', _why='alsoEvent')` is ambiguous.
    if _why and isinstance(event, string_types):
        raise ValueError('Both `_why` and `event` supplied.')
    # Two failures are ambiguous too.
    if not isinstance(_stuff, _FAIL_TYPES) and isinstance(event, _FAIL_TYPES):
        _why = _why or 'error'
        _stuff = event
    if isinstance(event, string_types):
        _why = event
    if not _stuff and sys.exc_info() != (None, None, None):
        _stuff = Failure()
    # Either we used the error ourselves or the user supplied one for
    # formatting.  Avoid log.err() to dump another traceback into the log.
    if isinstance(_stuff, BaseException):
        _stuff = Failure(_stuff)
    sys.exc_clear()
    return _stuff, _why, eventDict


class JSONRenderer(_JSONRenderer):
    """
    Behaves like :class:`structlog.processors.JSONRenderer` except that it
    formats tracebacks and failures itself if called with `err()`.

    *Not* an adapter like :class:`EventAdapter` but a real formatter.  Nor does
    it require to be adapted using it.
    """
    def __call__(self, logger, name, eventDict):
        _stuff, _why, eventDict = _extractStuffAndWhy(eventDict)
        if name == 'err':
            eventDict['event'] = _why
            if isinstance(_stuff, Failure):
                eventDict['exception'] = _stuff.getTraceback(detail='verbose')
                _stuff.cleanFailure()
        else:
            eventDict['event'] = _why
        return _JSONRenderer.__call__(self, logger, name, eventDict)


class EventAdapter(object):
    """
    Adapt an ``event_dict`` to Twisted logging system.

    Particularly, make a wrapped `twisted.python.log.err
    <http://twistedmatrix.com/documents/current/
    api/twisted.python.log.html#err>`_ behave as expected.

    **Must** be the last processor in the chain and requires a `dictFormatter`
    for the actual formatting as an constructor argument in order to be able to
    fully support the original behaviors of ``log.msg()`` and ``log.err()``.
    """
    def __init__(self, dictFormatter=None):
        """
        :param dictFormatter: A processor used to format the log message.
        """
        self._dictFormatter = dictFormatter or KeyValueRenderer()

    def __call__(self, logger, name, eventDict):
        if name == 'err':
            # This aspires to handle the following cases correctly:
            #   - log.err(failure, _why='event', **kw)
            #   - log.err('event', **kw)
            #   - log.err(_stuff=failure, _why='event', **kw)
            _stuff, _why, eventDict = _extractStuffAndWhy(eventDict)
            eventDict['event'] = _why
            return ((), {
                '_stuff': _stuff,
                '_why': self._dictFormatter(logger, name, eventDict),
            })
        else:
            return self._dictFormatter(logger, name, eventDict)
