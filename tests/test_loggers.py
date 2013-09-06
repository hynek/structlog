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

import re
import unittest

import pytest

from pretend import stub

from structlog.processors import KeyValueRenderer
from structlog.loggers import (
    BoundLogger,
    PrintLogger,
    ReturnLogger,
    _DEFAULT_CONTEXT_CLASS,
    _DEFAULT_PROCESSORS,
)


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
        assert '<PrintLogger()>' == repr(PrintLogger())


class TestBinding(object):
    def test_binds_independently(self):
        """
        Ensure BoundLogger is immutable by default.
        """
        b = BoundLogger.wrap(ReturnLogger(),
                             processors=[KeyValueRenderer(sort_keys=True)])
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
        b = BoundLogger.wrap(None)
        b = b.bind(x=42)
        assert 42 == b._context['x']
        b = b.bind()
        assert 42 == b._context['x']
        b = b.new()
        assert 'x' not in b._context

    def test_comparison(self):
        b = BoundLogger.wrap(None)
        assert b == b.bind()
        assert b is not b.bind()
        assert b != b.bind(x=5)
        assert b != 'test'


class TestWrapper(object):
    def test_caches(self):
        """
        __getattr__() gets called only once per logger method.
        """
        b = BoundLogger.wrap(ReturnLogger())
        assert 'msg' not in b.__dict__
        b.msg('foo')
        assert 'msg' in b.__dict__

    def test_copies_context_before_processing(self):
        def chk(_, __, event_dict):
            assert b._context is not event_dict
            return False

        b = BoundLogger.wrap(ReturnLogger, processors=[chk])
        b.msg('event')
        assert 'event' not in b._context

    def test_processor_returning_none_raises_valueerror(self):
        b = BoundLogger.wrap(ReturnLogger(), processors=[lambda *_: None])
        with pytest.raises(ValueError) as e:
            b.msg('boom')
        assert re.match(
            r'Processor \<function .+\> returned None.', e.value.args[0]
        )

    def test_processor_returning_false_silently_aborts_chain(self, capsys):
        # The 2nd processor would raise a ValueError if reached.
        b = BoundLogger.wrap(ReturnLogger(), processors=[lambda *_: False,
                                                         lambda *_: None])
        b.msg('silence!')
        assert ('', '') == capsys.readouterr()

    def test_processor_can_return_both_str_and_tuple(self):
        logger = stub(msg=lambda *args, **kw: (args, kw))
        b1 = BoundLogger.wrap(logger, processors=[lambda *_: 'foo'])
        b2 = BoundLogger.wrap(logger, processors=[lambda *_: (('foo',), {})])
        assert b1.msg('foo') == b2.msg('foo')

    def test_repr(self):
        l = BoundLogger.wrap(None, processors=[1, 2, 3], context_class=dict)
        assert '<BoundLogger(context={}, processors=[1, 2, 3])>' == repr(l)


class ConfigureTestCase(unittest.TestCase):
    """
    There's some global state here so we use a class to be able to clean up.
    """
    def setUp(self):
        self.b_def = BoundLogger.wrap(None)

    def tearDown(self):
        BoundLogger.reset_defaults()

    def test_reset(self):
        x = stub()
        BoundLogger.configure(processors=[x], context_class=dict)
        BoundLogger.reset_defaults()
        b = BoundLogger.wrap(None)
        assert x is not b._current_processors[0]
        assert self.b_def._current_processors == b._current_processors
        assert _DEFAULT_PROCESSORS == b._current_processors
        assert _DEFAULT_CONTEXT_CLASS == b._current_context_class

    def test_just_processors(self):
        x = stub()
        BoundLogger.configure(processors=[x])
        b = BoundLogger.wrap(None)
        assert x == b._current_processors[0]

    def test_just_context_class(self):
        BoundLogger.configure(context_class=dict)
        b = BoundLogger.wrap(None)
        assert dict is b._current_context_class

    def test_overwrite_processors(self):
        x = stub()
        z = stub()
        BoundLogger.configure(processors=[x])
        b = BoundLogger.wrap(None, processors=[z])
        assert 1 == len(b._current_processors)
        assert z is b._current_processors[0]

    def test_affects_all(self):
        x = stub()
        b = BoundLogger.wrap(None)
        BoundLogger.configure(processors=[x], context_class=dict)
        assert 1 == len(b._current_processors)
        assert x is b._current_processors[0]
        assert dict is b._current_context_class

    def test_bind_changes_type_of_dict_if_necessary(self):
        b = BoundLogger.wrap(None)
        b.configure(context_class=dict)
        assert _DEFAULT_CONTEXT_CLASS is b._context.__class__
        b = b.bind(x=42)
        assert _DEFAULT_CONTEXT_CLASS is not b._context.__class__
        assert dict is b._context.__class__

    def test_configure_does_not_affect_overwritten(self):
        """
        This is arguably an ugly test.  However it aspires to prove that any
        order of configuring and wrapping works as advertised.
        """
        x = stub()
        z = stub()
        BoundLogger.configure(processors=[x])
        b = BoundLogger.wrap(None, processors=[z], context_class=dict)
        part_def_b = BoundLogger.wrap(None)
        def_b1 = BoundLogger.wrap(None)
        BoundLogger.configure(processors=[x])
        assert 1 == len(b._current_processors)
        assert dict is b._current_context_class
        assert z is b._current_processors[0]
        def_b2 = BoundLogger.wrap(None)
        assert 1 == len(def_b1._current_processors)
        assert x is def_b1._current_processors[0]
        assert 1 == len(def_b2._current_processors)
        assert x is def_b2._current_processors[0]
        assert x is part_def_b._current_processors[0]
        assert (
            def_b1._current_processors is BoundLogger._default_processors
        )
        assert (
            def_b2._current_processors is BoundLogger._default_processors
        )
        assert (part_def_b._current_processors is
                BoundLogger._default_processors)
        assert dict is b._context_class

    def test_wrapper_converts_context_if_necessary(self):
        """
        If a logger logs without binding, the context is still of the default
        dict class instead of the one configured.

        In that case, the context gets converted first.
        """
        b = BoundLogger.wrap(ReturnLogger())
        BoundLogger.configure(context_class=dict)
        assert _DEFAULT_CONTEXT_CLASS is b._context.__class__
        b.info('event')
        assert _DEFAULT_CONTEXT_CLASS is not b._context.__class__
        assert dict is b._context.__class__

    def test_is_configured(self):
        b = BoundLogger.wrap(None)
        BoundLogger.configure()
        assert True is b.is_configured
        assert True is BoundLogger.is_configured
        BoundLogger.reset_defaults()
        assert False is b.is_configured
        assert False is BoundLogger.is_configured

    def test_configured_once(self):
        b = BoundLogger.wrap(None)
        BoundLogger.configure_once(context_class=dict)
        assert dict is b._current_context_class
        BoundLogger.configure_once(context_class=object)
        assert dict is b._current_context_class
