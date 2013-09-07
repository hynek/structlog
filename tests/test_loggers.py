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

from structlog._config import _CONFIG
from structlog._loggers import (
    BoundLogger,
    DropEvent,
    PrintLogger,
    ReturnLogger,
)
from structlog.processors import KeyValueRenderer


def test_return_logger():
    obj = ['hello']
    assert obj is ReturnLogger().msg(obj)


class TestPrintLogger(object):
    def test_prints_to_stdout_by_default(self, capsys):
        PrintLogger().msg('hello')
        out, err = capsys.readouterr()
        assert 'hello\n' == out
        assert '' == err

    def test_prints_to_correct_file(self, tmpdir, capsys):
        f = tmpdir.join('test.log')
        fo = f.open('w')
        PrintLogger(fo).msg('hello')
        out, err = capsys.readouterr()
        assert '' == out == err
        fo.close()
        assert 'hello\n' == f.read()

    def test_repr(self):
        assert repr(PrintLogger()).startswith(
            "<PrintLogger(file="
        )


def buildBL(logger=None, processors=None, context=None):
    """
    Convenience function to build BoundLoggers with sane defaults.
    """
    return BoundLogger(
        logger or ReturnLogger(),
        processors or _CONFIG.default_processors,
        context if context is not None else _CONFIG.default_context_class(),
    )


class TestBinding(object):
    def test_binds_independently(self):
        """
        Ensure BoundLogger is immutable by default.
        """
        b = buildBL(processors=[KeyValueRenderer(sort_keys=True)])
        b = b.bind(x=42, y=23)
        b1 = b.bind(foo='bar')
        assert (
            "event='event1' foo='bar' x=42 y=23 z=1" == b1.msg('event1', z=1)
        )
        assert (
            "event='event2' foo='bar' x=42 y=23 z=0" == b1.err('event2', z=0)
        )
        b2 = b.bind(foo='qux')
        assert (
            "event='event3' foo='qux' x=42 y=23 z=2" == b2.msg('event3', z=2)
        )
        assert (
            "event='event4' foo='qux' x=42 y=23 z=3" == b2.err('event4', z=3)
        )

    def test_new_clears_state(self):
        b = buildBL()
        b = b.bind(x=42)
        assert 42 == b._context['x']
        b = b.bind()
        assert 42 == b._context['x']
        b = b.new()
        assert 'x' not in b._context

    def test_comparison(self):
        b = buildBL()
        assert b == b.bind()
        assert b is not b.bind()
        assert b != b.bind(x=5)
        assert b != 'test'


class TestWrapper(object):
    def test_caches(self):
        """
        __getattr__() gets called only once per logger method.
        """
        b = buildBL()
        assert 'msg' not in b.__dict__
        b.msg('foo')
        assert 'msg' in b.__dict__

    def test_copies_context_before_processing(self):
        def chk(_, __, event_dict):
            assert b._context is not event_dict
            return ''

        b = buildBL(processors=[chk])
        b.msg('event')
        assert 'event' not in b._context

    def test_processor_raising_DropEvent_silently_aborts_chain(self, capsys):
        b = buildBL(processors=[raiser(DropEvent), raiser(ValueError)])
        b.msg('silence!')
        assert (('', '') == capsys.readouterr())

    def test_chain_does_not_swallow_all_exceptions(self):
        b = buildBL(processors=[raiser(ValueError)])
        with pytest.raises(ValueError):
            b.msg('boom')

    def test_processor_can_return_both_str_and_tuple(self):
        logger = stub(msg=lambda *args, **kw: (args, kw))
        b1 = buildBL(logger, processors=[lambda *_: 'foo'])
        b2 = buildBL(logger, processors=[lambda *_: (('foo',), {})])
        assert b1.msg('foo') == b2.msg('foo')

    def test_repr(self):
        l = buildBL(processors=[1, 2, 3], context={})
        assert '<BoundLogger(context={}, processors=[1, 2, 3])>' == repr(l)
