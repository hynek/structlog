# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Processors and tools specific to the `Twisted <https://twistedmatrix.com/>`_
networking engine.

See also :doc:`structlog's Twisted support <twisted>`.
"""

from __future__ import absolute_import, division, print_function

import json
import sys

from six import PY2, string_types
from twisted.python import log
from twisted.python.failure import Failure
from twisted.python.log import ILogObserver, textFromEventDict
from zope.interface import implementer

from structlog._base import BoundLoggerBase
from structlog._utils import until_not_interrupted
from structlog.processors import (
    # can't import processors module without risking circular imports
    JSONRenderer as GenericJSONRenderer,
    KeyValueRenderer,
)


class BoundLogger(BoundLoggerBase):
    """
    Twisted-specific version of :class:`structlog.BoundLogger`.

    Works exactly like the generic one except that it takes advantage of
    knowing the logging methods in advance.

    Use it like::

        configure(
            wrapper_class=structlog.twisted.BoundLogger,
        )

    """
    def msg(self, event=None, **kw):
        """
        Process event and call ``log.msg()`` with the result.
        """
        return self._proxy_to_logger('msg', event, **kw)

    def err(self, event=None, **kw):
        """
        Process event and call ``log.err()`` with the result.
        """
        return self._proxy_to_logger('err', event, **kw)


class LoggerFactory(object):
    """
    Build a Twisted logger when an *instance* is called.

    >>> from structlog import configure
    >>> from structlog.twisted import LoggerFactory
    >>> configure(logger_factory=LoggerFactory())
    """
    def __call__(self, *args):
        """
        Positional arguments are silently ignored.

        :rvalue: A new Twisted logger.

        .. versionchanged:: 0.4.0
            Added support for optional positional arguments.
        """
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
    if PY2:
        sys.exc_clear()
    return _stuff, _why, eventDict


class ReprWrapper(object):
    """
    Wrap a string and return it as the __repr__.

    This is needed for log.err() that calls repr() on _stuff:

    >>> repr("foo")
    "'foo'"
    >>> repr(ReprWrapper("foo"))
    'foo'

    Note the extra quotes in the unwrapped example.
    """
    def __init__(self, string):
        self.string = string

    def __eq__(self, other):
        """
        Check for equality, actually just for tests.
        """
        return isinstance(other, self.__class__) \
            and self.string == other.string

    def __repr__(self):
        return self.string


class JSONRenderer(GenericJSONRenderer):
    """
    Behaves like :class:`structlog.processors.JSONRenderer` except that it
    formats tracebacks and failures itself if called with `err()`.

    .. note::

        This ultimately means that the messages get logged out using `msg()`,
        and *not* `err()` which renders failures in separate lines.

        Therefore it will break your tests that contain assertions using
        `flushLoggedErrors <https://twistedmatrix.com/documents/
        current/api/twisted.trial.unittest.SynchronousTestCase.html
        #flushLoggedErrors>`_.

    *Not* an adapter like :class:`EventAdapter` but a real formatter.  Nor does
    it require to be adapted using it.

    Use together with a :class:`JSONLogObserverWrapper`-wrapped Twisted logger
    like :func:`plainJSONStdOutLogger` for pure-JSON logs.
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
        return ((ReprWrapper(
            GenericJSONRenderer.__call__(self, logger, name, eventDict)
        ),), {'_structlog': True})


@implementer(ILogObserver)
class PlainFileLogObserver(object):
    """
    Write only the the plain message without timestamps or anything else.

    Great to just print JSON to stdout where you catch it with something like
    runit.

    :param file file: File to print to.


    .. versionadded:: 0.2.0
    """
    def __init__(self, file):
        self._write = file.write
        self._flush = file.flush

    def __call__(self, eventDict):
        until_not_interrupted(self._write, textFromEventDict(eventDict) + '\n')
        until_not_interrupted(self._flush)


@implementer(ILogObserver)
class JSONLogObserverWrapper(object):
    """
    Wrap a log *observer* and render non-:class:`JSONRenderer` entries to JSON.

    :param ILogObserver observer: Twisted log observer to wrap.  For example
        :class:`PlainFileObserver` or Twisted's stock `FileLogObserver
        <https://twistedmatrix.com/documents/current/api/twisted.python.log.
        FileLogObserver.html>`_

    .. versionadded:: 0.2.0
    """
    def __init__(self, observer):
        self._observer = observer

    def __call__(self, eventDict):
        if '_structlog' not in eventDict:
            eventDict['message'] = (json.dumps({
                'event': textFromEventDict(eventDict),
                'system': eventDict.get('system'),
            }),)
            eventDict['_structlog'] = True
        return self._observer(eventDict)


def plainJSONStdOutLogger():
    """
    Return a logger that writes only the message to stdout.

    Transforms non-:class:`~structlog.twisted.JSONRenderer` messages to JSON.

    Ideal for JSONifying log entries from Twisted plugins and libraries that
    are outside of your control::

        $ twistd -n --logger structlog.twisted.plainJSONStdOutLogger web
        {"event": "Log opened.", "system": "-"}
        {"event": "twistd 13.1.0 (python 2.7.3) starting up.", "system": "-"}
        {"event": "reactor class: twisted...EPollReactor.", "system": "-"}
        {"event": "Site starting on 8080", "system": "-"}
        {"event": "Starting factory <twisted.web.server.Site ...>", ...}
        ...

    Composes :class:`PlainFileLogObserver` and :class:`JSONLogObserverWrapper`
    to a usable logger.

    .. versionadded:: 0.2.0
    """
    return JSONLogObserverWrapper(PlainFileLogObserver(sys.stdout))


class EventAdapter(object):
    """
    Adapt an ``event_dict`` to Twisted logging system.

    Particularly, make a wrapped `twisted.python.log.err
    <https://twistedmatrix.com/documents/current/
    api/twisted.python.log.html#err>`_ behave as expected.

    :param callable dictRenderer: Renderer that is used for the actual
        log message.  Please note that structlog comes with a dedicated
        :class:`JSONRenderer`.

    **Must** be the last processor in the chain and requires a `dictRenderer`
    for the actual formatting as an constructor argument in order to be able to
    fully support the original behaviors of ``log.msg()`` and ``log.err()``.
    """
    def __init__(self, dictRenderer=None):
        """
        :param dictRenderer: A processor used to format the log message.
        """
        self._dictRenderer = dictRenderer or KeyValueRenderer()

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
                '_why': self._dictRenderer(logger, name, eventDict),
            })
        else:
            return self._dictRenderer(logger, name, eventDict)
