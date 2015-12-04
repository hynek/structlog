# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import absolute_import, division, print_function

import pytest

from pretend import raiser, stub

from structlog._base import BoundLoggerBase
from structlog._config import _CONFIG
from structlog._loggers import ReturnLogger
from structlog.exceptions import DropEvent
from structlog.processors import KeyValueRenderer


def build_bl(logger=None, processors=None, context=None):
    """
    Convenience function to build BoundLoggerBases with sane defaults.
    """
    return BoundLoggerBase(
        logger or ReturnLogger(),
        processors or _CONFIG.default_processors,
        context if context is not None else _CONFIG.default_context_class(),
    )


class TestBinding(object):
    def test_repr(self):
        l = build_bl(processors=[1, 2, 3], context={})
        assert '<BoundLoggerBase(context={}, processors=[1, 2, 3])>' == repr(l)

    def test_binds_independently(self):
        """
        Ensure BoundLogger is immutable by default.
        """
        b = build_bl(processors=[KeyValueRenderer(sort_keys=True)])
        b = b.bind(x=42, y=23)
        b1 = b.bind(foo='bar')
        b2 = b.bind(foo='qux')
        assert b._context != b1._context != b2._context

    def test_new_clears_state(self):
        b = build_bl()
        b = b.bind(x=42)
        assert 42 == b._context['x']
        b = b.bind()
        assert 42 == b._context['x']
        b = b.new()
        assert 'x' not in b._context

    def test_comparison(self):
        b = build_bl()
        assert b == b.bind()
        assert b is not b.bind()
        assert b != b.bind(x=5)
        assert b != 'test'

    def test_bind_keeps_class(self):
        class Wrapper(BoundLoggerBase):
            pass
        b = Wrapper(None, [], {})
        assert isinstance(b.bind(), Wrapper)

    def test_new_keeps_class(self):
        class Wrapper(BoundLoggerBase):
            pass
        b = Wrapper(None, [], {})
        assert isinstance(b.new(), Wrapper)

    def test_unbind(self):
        b = build_bl().bind(x=42, y=23).unbind('x', 'y')
        assert {} == b._context


class TestProcessing(object):
    def test_copies_context_before_processing(self):
        """
        BoundLoggerBase._process_event() gets called before relaying events
        to wrapped loggers.
        """
        def chk(_, __, event_dict):
            assert b._context is not event_dict
            return ''

        b = build_bl(processors=[chk])
        assert (('',), {}) == b._process_event('', 'event', {})
        assert 'event' not in b._context

    def test_chain_does_not_swallow_all_exceptions(self):
        b = build_bl(processors=[raiser(ValueError)])
        with pytest.raises(ValueError):
            b._process_event('', 'boom', {})

    def test_last_processor_returns_string(self):
        """
        If the final processor returns a string, ``(the_string,), {}`` is
        returned.
        """
        logger = stub(msg=lambda *args, **kw: (args, kw))
        b = build_bl(logger, processors=[lambda *_: 'foo'])
        assert (
            (('foo',), {}) ==
            b._process_event('', 'foo', {})
        )

    def test_last_processor_returns_tuple(self):
        """
        If the final processor returns a tuple, it is just passed through.
        """
        logger = stub(msg=lambda *args, **kw: (args, kw))
        b = build_bl(logger, processors=[lambda *_: (('foo',),
                                                     {'key': 'value'})])
        assert (
            (('foo',), {'key': 'value'}) ==
            b._process_event('', 'foo', {})
        )

    def test_last_processor_returns_dict(self):
        """
        If the final processor returns a dict, ``(), the_dict`` is returnend.
        """
        logger = stub(msg=lambda *args, **kw: (args, kw))
        b = build_bl(logger, processors=[lambda *_: {'event': 'foo'}])
        assert (
            ((), {'event': 'foo'}) ==
            b._process_event('', 'foo', {})
        )

    def test_last_processor_returns_unknown_value(self):
        """
        If the final processor returns something unexpected, raise ValueError
        with a helpful error message.
        """
        logger = stub(msg=lambda *args, **kw: (args, kw))
        b = build_bl(logger, processors=[lambda *_: object()])
        with pytest.raises(ValueError) as exc:
            b._process_event('', 'foo', {})

        assert (
            exc.value.args[0].startswith("Last processor didn't return")
        )


class TestProxying(object):
    def test_processor_raising_DropEvent_silently_aborts_chain(self, capsys):
        b = build_bl(processors=[raiser(DropEvent), raiser(ValueError)])
        b._proxy_to_logger('', None, x=5)
        assert (('', '') == capsys.readouterr())
