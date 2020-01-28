# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.


import json

from collections import OrderedDict
from io import StringIO

import pytest

from pretend import call_recorder
from twisted.python.failure import Failure
from twisted.python.log import ILogObserver

from structlog import ReturnLogger
from structlog._config import _CONFIG
from structlog.processors import KeyValueRenderer
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
        processors or [KeyValueRenderer()],
        context if context is not None else _CONFIG.default_context_class(),
    )


class TestBoundLogger:
    def test_msg(self):
        """
        log.msg renders correctly.
        """
        bl = build_bl()

        assert "foo=42 event='event'" == bl.msg("event", foo=42)

    def test_errVanilla(self):
        """
        log.err renders correctly if no failure is attached.
        """
        bl = build_bl()

        assert "foo=42 event='event'" == bl.err("event", foo=42)

    def test_errWithFailure(self):
        """
        Failures are correctly injected into the log entries.
        """
        bl = build_bl(
            processors=[EventAdapter(dictRenderer=KeyValueRenderer())]
        )
        try:
            raise ValueError
        except ValueError:
            # Use str() for comparison to avoid tricky
            # deep-compares of Failures.
            assert str(
                (
                    (),
                    {
                        "_stuff": Failure(ValueError()),
                        "_why": "foo=42 event='event'",
                    },
                )
            ) == str(bl.err("event", foo=42))


class TestExtractStuffAndWhy:
    def test_extractFailsOnTwoFailures(self):
        """
        Raise ValueError if both _stuff and event contain exceptions.
        """
        with pytest.raises(ValueError) as e:
            _extractStuffAndWhy(
                {
                    "_stuff": Failure(ValueError()),
                    "event": Failure(TypeError()),
                }
            )

        assert (
            "Both _stuff and event contain an Exception/Failure."
            == e.value.args[0]
        )

    def test_failsOnConflictingEventAnd_why(self):
        """
        Raise ValueError if both _why and event are in the event_dict.
        """
        with pytest.raises(ValueError) as e:
            _extractStuffAndWhy({"_why": "foo", "event": "bar"})

        assert "Both `_why` and `event` supplied." == e.value.args[0]

    def test_handlesFailures(self):
        """
        Extracts failures and events.
        """
        f = Failure(ValueError())

        assert ({"value": f}, "foo", {}) == _extractStuffAndWhy(
            {"_why": "foo", "_stuff": {"value": f}}
        )
        assert ({"value": f}, None, {}) == _extractStuffAndWhy(
            {"_stuff": {"value": f}}
        )

    def test_handlesMissingFailure(self):
        """
        Missing failures extract a None.
        """
        assert (None, "foo", {}) == _extractStuffAndWhy({"event": "foo"})


class TestEventAdapter:
    """
    Some tests here are redundant because they predate _extractStuffAndWhy.
    """

    def test_EventAdapterFormatsLog(self):
        la = EventAdapter(_render_repr)

        assert "{'foo': 'bar'}" == la(None, "msg", {"foo": "bar"})

    def test_transforms_whyIntoEvent(self):
        """
        log.err(_stuff=exc, _why='foo') makes the output 'event="foo"'
        """
        la = EventAdapter(_render_repr)
        error = ValueError("test")
        rv = la(None, "err", {"_stuff": error, "_why": "foo", "event": None})

        assert () == rv[0]
        assert isinstance(rv[1]["_stuff"], Failure)
        assert error == rv[1]["_stuff"].value
        assert "{'event': 'foo'}" == rv[1]["_why"]

    def test_worksUsualCase(self):
        """
        log.err(exc, _why='foo') makes the output 'event="foo"'
        """
        la = EventAdapter(_render_repr)
        error = ValueError("test")
        rv = la(None, "err", {"event": error, "_why": "foo"})

        assert () == rv[0]
        assert isinstance(rv[1]["_stuff"], Failure)
        assert error == rv[1]["_stuff"].value
        assert "{'event': 'foo'}" == rv[1]["_why"]

    def test_allKeywords(self):
        """
        log.err(_stuff=exc, _why='event')
        """
        la = EventAdapter(_render_repr)
        error = ValueError("test")
        rv = la(None, "err", {"_stuff": error, "_why": "foo"})

        assert () == rv[0]
        assert isinstance(rv[1]["_stuff"], Failure)
        assert error == rv[1]["_stuff"].value
        assert "{'event': 'foo'}" == rv[1]["_why"]

    def test_noFailure(self):
        """
        log.err('event')
        """
        la = EventAdapter(_render_repr)

        assert ((), {"_stuff": None, "_why": "{'event': 'someEvent'}"}) == la(
            None, "err", {"event": "someEvent"}
        )

    def test_noFailureWithKeyword(self):
        """
        log.err(_why='event')
        """
        la = EventAdapter(_render_repr)

        assert ((), {"_stuff": None, "_why": "{'event': 'someEvent'}"}) == la(
            None, "err", {"_why": "someEvent"}
        )

    def test_catchesConflictingEventAnd_why(self):
        la = EventAdapter(_render_repr)

        with pytest.raises(ValueError) as e:
            la(None, "err", {"event": "someEvent", "_why": "someReason"})

        assert "Both `_why` and `event` supplied." == e.value.args[0]


@pytest.fixture
def jr():
    """
    A plain Twisted JSONRenderer.
    """
    return JSONRenderer()


class TestJSONRenderer:
    def test_dumpsKWsAreHandedThrough(self, jr):
        """
        JSONRenderer allows for setting arguments that are passed to
        json.dumps().  Make sure they are passed.
        """
        d = OrderedDict(x="foo")
        d.update(a="bar")
        jr_sorted = JSONRenderer(sort_keys=True)

        assert jr_sorted(None, "err", d) != jr(None, "err", d)

    def test_handlesMissingFailure(self, jr):
        """
        Calling err without an actual failure works and returns the event as
        a string wrapped in ReprWrapper.
        """
        assert (
            ReprWrapper('{"event": "foo"}')
            == jr(None, "err", {"event": "foo"})[0][0]
        )
        assert (
            ReprWrapper('{"event": "foo"}')
            == jr(None, "err", {"_why": "foo"})[0][0]
        )

    def test_msgWorksToo(self, jr):
        """
        msg renders the event as a string and wraps it using ReprWrapper.
        """
        assert (
            ReprWrapper('{"event": "foo"}')
            == jr(None, "msg", {"_why": "foo"})[0][0]
        )

    def test_handlesFailure(self, jr):
        rv = jr(None, "err", {"event": Failure(ValueError())})[0][0].string

        assert "Failure: builtins.ValueError" in rv
        assert '"event": "error"' in rv

    def test_setsStructLogField(self, jr):
        """
        Formatted entries are marked so they can be identified without guessing
        for example in JSONLogObserverWrapper.
        """
        assert {"_structlog": True} == jr(None, "msg", {"_why": "foo"})[1]


class TestReprWrapper:
    def test_repr(self):
        """
        The repr of the wrapped string is the vanilla string without quotes.
        """
        assert "foo" == repr(ReprWrapper("foo"))


class TestPlainFileLogObserver:
    def test_isLogObserver(self):
        assert ILogObserver.providedBy(PlainFileLogObserver(StringIO()))

    def test_writesOnlyMessageWithLF(self):
        sio = StringIO()
        PlainFileLogObserver(sio)(
            {"system": "some system", "message": ("hello",)}
        )

        assert "hello\n" == sio.getvalue()


class TestJSONObserverWrapper:
    def test_IsAnObserver(self):
        assert ILogObserver.implementedBy(JSONLogObserverWrapper)

    def test_callsWrappedObserver(self):
        """
        The wrapper always runs the wrapped observer in the end.
        """
        o = call_recorder(lambda *a, **kw: None)
        JSONLogObserverWrapper(o)({"message": ("hello",)})

        assert 1 == len(o.calls)

    def test_jsonifiesPlainLogEntries(self):
        """
        Entries that aren't formatted by JSONRenderer are rendered as JSON
        now.
        """
        o = call_recorder(lambda *a, **kw: None)
        JSONLogObserverWrapper(o)({"message": ("hello",), "system": "-"})
        msg = json.loads(o.calls[0].args[0]["message"][0])

        assert msg == {"event": "hello", "system": "-"}

    def test_leavesStructLogAlone(self):
        """
        Entries that are formatted by JSONRenderer are left alone.
        """
        d = {"message": ("hello",), "_structlog": True}

        def verify(eventDict):
            assert d == eventDict

        JSONLogObserverWrapper(verify)(d)


class TestPlainJSONStdOutLogger:
    def test_isLogObserver(self):
        assert ILogObserver.providedBy(plainJSONStdOutLogger())
