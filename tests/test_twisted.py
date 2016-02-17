# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import absolute_import, division, print_function

import json

from collections import OrderedDict

import pytest

from pretend import call_recorder
from six import PY3
from six.moves import cStringIO as StringIO
from twisted.python.failure import Failure, NoCurrentExceptionError
from twisted.python.log import ILogObserver

from structlog._config import _CONFIG
from structlog._loggers import ReturnLogger
from structlog.twisted import (
    BoundLogger,
    EventAdapter,
    JSONLogObserverWrapper,
    JSONRenderer,
    LoggerFactory,
    PlainFileLogObserver,
    ReprWrapper,
    _extractStuffAndWhy,
    plainJSONStdOutLogger,
)


def test_LoggerFactory():
    from twisted.python import log
    assert log is LoggerFactory()()


def _render_repr(_, __, event_dict):
    return repr(event_dict)


def build_bl(logger=None, processors=None, context=None):
    """
    Convenience function to build BoundLoggerses with sane defaults.
    """
    return BoundLogger(
        logger or ReturnLogger(),
        processors or _CONFIG.default_processors,
        context if context is not None else _CONFIG.default_context_class(),
    )


class TestBoundLogger(object):
    def test_msg(self):
        bl = build_bl()
        assert "foo=42 event='event'" == bl.msg('event', foo=42)

    def test_errVanilla(self):
        bl = build_bl()
        assert "foo=42 event='event'" == bl.err('event', foo=42)

    def test_errWithFailure(self):
        bl = build_bl(processors=[EventAdapter()])
        try:
            raise ValueError
        except ValueError:
            # Use str() for comparison to avoid tricky
            # deep-compares of Failures.
            assert (
                str(((), {'_stuff': Failure(ValueError()),
                          '_why': "foo=42 event='event'"})) ==
                str(bl.err('event', foo=42))
            )


class TestExtractStuffAndWhy(object):
    def test_extractFailsOnTwoFailures(self):
        """
        Raise ValueError if both _stuff and event contain exceptions.
        """
        with pytest.raises(ValueError) as e:
            _extractStuffAndWhy({'_stuff': Failure(ValueError()),
                                 'event': Failure(TypeError())})
        assert (
            "Both _stuff and event contain an Exception/Failure." ==
            e.value.args[0]
        )

    def test_failsOnConflictingEventAnd_why(self):
        """
        Raise ValueError if both _why and event are in the event_dict.
        """
        with pytest.raises(ValueError) as e:
            _extractStuffAndWhy({'_why': 'foo', 'event': 'bar'})
        assert (
            "Both `_why` and `event` supplied." ==
            e.value.args[0]
        )

    def test_handlesFailures(self):
        """
        Extracts failures and events.
        """
        f = Failure(ValueError())
        assert (
            (f, "foo", {}) ==
            _extractStuffAndWhy({"_why": "foo",
                                 "_stuff": f})
        )
        assert (
            (f, None, {}) ==
            _extractStuffAndWhy({"_stuff": f})
        )

    def test_handlesMissingFailure(self):
        """
        Missing failures extract a None.
        """
        assert (
            (None, "foo", {}) ==
            _extractStuffAndWhy({"event": "foo"})
        )

    @pytest.mark.xfail(PY3, reason="Py3 does not allow for cleaning exc_info")
    def test_recognizesErrorsAndCleansThem(self):
        """
        If no error is supplied, the environment is checked for one.  If one is
        found, it's used and cleared afterwards so log.err doesn't add it as
        well.
        """
        try:
            raise ValueError
        except ValueError:
            f = Failure()
            _stuff, _why, ed = _extractStuffAndWhy({'event': 'foo'})
            assert _stuff.value is f.value
            with pytest.raises(NoCurrentExceptionError):
                Failure()


class TestEventAdapter(object):
    """
    Some tests here are redundant because they predate _extractStuffAndWhy.
    """
    def test_EventAdapterFormatsLog(self):
        la = EventAdapter(_render_repr)
        assert "{'foo': 'bar'}" == la(None, 'msg', {'foo': 'bar'})

    def test_transforms_whyIntoEvent(self):
        """
        log.err(_stuff=exc, _why='foo') makes the output 'event="foo"'
        """
        la = EventAdapter(_render_repr)
        error = ValueError('test')
        rv = la(None, 'err', {
            '_stuff': error,
            '_why': 'foo',
            'event': None,
        })
        assert () == rv[0]
        assert isinstance(rv[1]['_stuff'], Failure)
        assert error == rv[1]['_stuff'].value
        assert "{'event': 'foo'}" == rv[1]['_why']

    def test_worksUsualCase(self):
        """
        log.err(exc, _why='foo') makes the output 'event="foo"'
        """
        la = EventAdapter(_render_repr)
        error = ValueError('test')
        rv = la(None, 'err', {'event': error, '_why': 'foo'})
        assert () == rv[0]
        assert isinstance(rv[1]['_stuff'], Failure)
        assert error == rv[1]['_stuff'].value
        assert "{'event': 'foo'}" == rv[1]['_why']

    def test_allKeywords(self):
        """
        log.err(_stuff=exc, _why='event')
        """
        la = EventAdapter(_render_repr)
        error = ValueError('test')
        rv = la(None, 'err', {'_stuff': error, '_why': 'foo'})
        assert () == rv[0]
        assert isinstance(rv[1]['_stuff'], Failure)
        assert error == rv[1]['_stuff'].value
        assert "{'event': 'foo'}" == rv[1]['_why']

    def test_noFailure(self):
        """
        log.err('event')
        """
        la = EventAdapter(_render_repr)
        assert ((), {
            '_stuff': None,
            '_why': "{'event': 'someEvent'}",
        }) == la(None, 'err', {
            'event': 'someEvent'
        })

    def test_noFailureWithKeyword(self):
        """
        log.err(_why='event')
        """
        la = EventAdapter(_render_repr)
        assert ((), {
            '_stuff': None,
            '_why': "{'event': 'someEvent'}",
        }) == la(None, 'err', {
            '_why': 'someEvent'
        })

    def test_catchesConflictingEventAnd_why(self):
        la = EventAdapter(_render_repr)
        with pytest.raises(ValueError) as e:
            la(None, 'err', {
                'event': 'someEvent',
                '_why': 'someReason',
            })
        assert 'Both `_why` and `event` supplied.' == e.value.args[0]


@pytest.fixture
def jr():
    """
    A plain Twisted JSONRenderer.
    """
    return JSONRenderer()


class TestJSONRenderer(object):
    def test_dumpsKWsAreHandedThrough(self, jr):
        """
        JSONRenderer allows for setting arguments that are passed to
        json.dumps().  Make sure they are passed.
        """
        d = OrderedDict(x='foo')
        d.update(a='bar')
        jr_sorted = JSONRenderer(sort_keys=True)
        assert jr_sorted(None, 'err', d) != jr(None, 'err', d)

    def test_handlesMissingFailure(self, jr):
        """
        Calling err without an actual failure works and returns the event as
        a string wrapped in ReprWrapper.
        """
        assert ReprWrapper(
            '{"event": "foo"}'
        ) == jr(None, "err", {"event": "foo"})[0][0]
        assert ReprWrapper(
            '{"event": "foo"}'
        ) == jr(None, "err", {"_why": "foo"})[0][0]

    def test_msgWorksToo(self, jr):
        """
        msg renders the event as a string and wraps it using ReprWrapper.
        """
        assert ReprWrapper(
            '{"event": "foo"}'
        ) == jr(None, 'msg', {'_why': 'foo'})[0][0]

    def test_handlesFailure(self, jr):
        rv = jr(None, 'err', {'event': Failure(ValueError())})[0][0].string
        assert 'Failure: {0}.ValueError'.format("builtins"
                                                if PY3
                                                else "exceptions") in rv
        assert '"event": "error"' in rv

    def test_setsStructLogField(self, jr):
        """
        Formatted entries are marked so they can be identified without guessing
        for example in JSONLogObserverWrapper.
        """
        assert {'_structlog': True} == jr(None, 'msg', {'_why': 'foo'})[1]


class TestReprWrapper(object):
    def test_repr(self):
        """
        The repr of the wrapped string is the vanilla string without quotes.
        """
        assert "foo" == repr(ReprWrapper("foo"))


class TestPlainFileLogObserver(object):
    def test_isLogObserver(self):
        assert ILogObserver.providedBy(PlainFileLogObserver(StringIO()))

    def test_writesOnlyMessageWithLF(self):
        sio = StringIO()
        PlainFileLogObserver(sio)({'system': 'some system',
                                   'message': ('hello',)})
        assert 'hello\n' == sio.getvalue()


class TestJSONObserverWrapper(object):
    def test_IsAnObserver(self):
        assert ILogObserver.implementedBy(JSONLogObserverWrapper)

    def test_callsWrappedObserver(self):
        """
        The wrapper always runs the wrapped observer in the end.
        """
        o = call_recorder(lambda *a, **kw: None)
        JSONLogObserverWrapper(o)({'message': ('hello',)})
        assert 1 == len(o.calls)

    def test_jsonifiesPlainLogEntries(self):
        """
        Entries that aren't formatted by JSONRenderer are rendered as JSON
        now.
        """
        o = call_recorder(lambda *a, **kw: None)
        JSONLogObserverWrapper(o)({'message': ('hello',), 'system': '-'})
        msg = json.loads(o.calls[0].args[0]['message'][0])
        assert msg == {'event': 'hello', 'system': '-'}

    def test_leavesStructLogAlone(self):
        """
        Entries that are formatted by JSONRenderer are left alone.
        """
        d = {'message': ('hello',), '_structlog': True}

        def verify(eventDict):
            assert d == eventDict

        JSONLogObserverWrapper(verify)(d)


class TestPlainJSONStdOutLogger(object):
    def test_isLogObserver(self):
        assert ILogObserver.providedBy(plainJSONStdOutLogger())
