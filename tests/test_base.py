# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.


import pytest

from pretend import raiser, stub

from structlog import get_context
from structlog._base import BoundLoggerBase
from structlog._config import _CONFIG
from structlog.exceptions import DropEvent
from structlog.processors import KeyValueRenderer
from structlog.testing import ReturnLogger


def build_bl(logger=None, processors=None, context=None):
    """
    Convenience function to build BoundLoggerBases with sane defaults.
    """
    return BoundLoggerBase(
        logger if logger is not None else ReturnLogger(),
        processors if processors is not None else _CONFIG.default_processors,
        context if context is not None else _CONFIG.default_context_class(),
    )


class TestBinding:
    def test_repr(self):
        bl = build_bl(processors=[1, 2, 3], context={})

        assert ("<BoundLoggerBase(context={}, processors=[1, 2, 3])>") == repr(
            bl
        )

    def test_binds_independently(self):
        """
        Ensure BoundLogger is immutable by default.
        """
        b = build_bl(processors=[KeyValueRenderer(sort_keys=True)])
        b = b.bind(x=42, y=23)
        b1 = b.bind(foo="bar")
        b2 = b.bind(foo="qux")

        assert b._context != b1._context != b2._context

    def test_new_clears_state(self):
        """
        Calling new() on a logger clears the context.
        """
        b = build_bl()
        b = b.bind(x=42)

        assert 42 == get_context(b)["x"]

        b = b.bind()

        assert 42 == get_context(b)["x"]

        b = b.new()

        assert {} == dict(get_context(b))

    def test_comparison(self):
        """
        Two bound loggers are equal if their context is equal.
        """
        b = build_bl()

        assert b == b.bind()
        assert b is not b.bind()
        assert b != b.bind(x=5)
        assert b != "test"

    def test_bind_keeps_class(self):
        """
        Binding values does not change the type of the bound logger.
        """

        class Wrapper(BoundLoggerBase):
            pass

        b = Wrapper(None, [], {})

        assert isinstance(b.bind(), Wrapper)

    def test_new_keeps_class(self):
        """
        Clearing context does not change the type of the bound logger.
        """

        class Wrapper(BoundLoggerBase):
            pass

        b = Wrapper(None, [], {})

        assert isinstance(b.new(), Wrapper)

    def test_unbind(self):
        """
        unbind() removes keys from context.
        """
        b = build_bl().bind(x=42, y=23).unbind("x", "y")

        assert {} == b._context

    def test_unbind_fail(self):
        """
        unbind() raises KeyError if the key is missing.
        """
        with pytest.raises(KeyError):
            build_bl().bind(x=42, y=23).unbind("x", "z")

    def test_try_unbind(self):
        """
        try_unbind() removes keys from context.
        """
        b = build_bl().bind(x=42, y=23).try_unbind("x", "y")

        assert {} == b._context

    def test_try_unbind_fail(self):
        """
        try_unbind() does nothing if the key is missing.
        """
        b = build_bl().bind(x=42, y=23).try_unbind("x", "z")

        assert {"y": 23} == b._context


class TestProcessing:
    def test_event_empty_string(self):
        """
        Empty strings are a valid event.
        """
        b = build_bl(processors=[], context={})

        args, kw = b._process_event("meth", "", {"foo": "bar"})

        assert () == args
        assert {"event": "", "foo": "bar"} == kw

    def test_copies_context_before_processing(self):
        """
        BoundLoggerBase._process_event() gets called before relaying events
        to wrapped loggers.
        """

        def chk(_, __, event_dict):
            assert b._context is not event_dict
            return ""

        b = build_bl(processors=[chk])

        assert (("",), {}) == b._process_event("", "event", {})
        assert "event" not in b._context

    def test_chain_does_not_swallow_all_exceptions(self):
        b = build_bl(processors=[raiser(ValueError)])
        with pytest.raises(ValueError):
            b._process_event("", "boom", {})

    def test_last_processor_returns_string(self):
        """
        If the final processor returns a string, ``(the_string,), {}`` is
        returned.
        """
        logger = stub(msg=lambda *args, **kw: (args, kw))
        b = build_bl(logger, processors=[lambda *_: "foo"])

        assert (("foo",), {}) == b._process_event("", "foo", {})

    def test_last_processor_returns_tuple(self):
        """
        If the final processor returns a tuple, it is just passed through.
        """
        logger = stub(msg=lambda *args, **kw: (args, kw))
        b = build_bl(
            logger, processors=[lambda *_: (("foo",), {"key": "value"})]
        )

        assert (("foo",), {"key": "value"}) == b._process_event("", "foo", {})

    def test_last_processor_returns_dict(self):
        """
        If the final processor returns a dict, ``(), the_dict`` is returned.
        """
        logger = stub(msg=lambda *args, **kw: (args, kw))
        b = build_bl(logger, processors=[lambda *_: {"event": "foo"}])

        assert ((), {"event": "foo"}) == b._process_event("", "foo", {})

    def test_last_processor_returns_unknown_value(self):
        """
        If the final processor returns something unexpected, raise ValueError
        with a helpful error message.
        """
        logger = stub(msg=lambda *args, **kw: (args, kw))
        b = build_bl(logger, processors=[lambda *_: object()])
        with pytest.raises(ValueError) as exc:
            b._process_event("", "foo", {})

        assert exc.value.args[0].startswith("Last processor didn't return")


class TestProxying:
    def test_processor_raising_DropEvent_silently_aborts_chain(self, capsys):
        """
        If a processor raises DropEvent, the chain is aborted and nothing is
        proxied to the logger.
        """
        b = build_bl(processors=[raiser(DropEvent), raiser(ValueError)])
        b._proxy_to_logger("", None, x=5)

        assert ("", "") == capsys.readouterr()
