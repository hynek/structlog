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

from __future__ import absolute_import, division, print_function

import pytest

from pretend import raiser, stub

from structlog._base import BoundLoggerBase
from structlog._config import _CONFIG
from structlog._exc import DropEvent
from structlog._loggers import ReturnLogger
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

    def test_processor_can_return_both_str_and_tuple(self):
        logger = stub(msg=lambda *args, **kw: (args, kw))
        b1 = build_bl(logger, processors=[lambda *_: 'foo'])
        b2 = build_bl(logger, processors=[lambda *_: (('foo',), {})])
        assert (
            b1._process_event('', 'foo', {})
            == b2._process_event('', 'foo', {})
        )


class TestProxying(object):
    def test_processor_raising_DropEvent_silently_aborts_chain(self, capsys):
        b = build_bl(processors=[raiser(DropEvent), raiser(ValueError)])
        b._proxy_to_logger('', None, x=5)
        assert (('', '') == capsys.readouterr())
