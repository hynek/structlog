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

import threading

import pytest

from structlog import BoundLogger, ReturnLogger
from structlog._compat import OrderedDict
from structlog.threadlocal import wrap_dict, tmp_bind


@pytest.fixture
def D():
    """
    Returns a dict wrapped in _ThreadLocalDictWrapper.
    """
    return wrap_dict(dict)


@pytest.fixture
def OD():
    """
    Returns an OrderedDict wrapped in _ThreadLocalDictWrapper.
    """
    return wrap_dict(OrderedDict)


@pytest.fixture
def logger():
    """
    Returns a simple logger stub with a *msg* method that takes one argument
    which gets returned.
    """
    return ReturnLogger()


class TestTmpBind(object):
    def tearDown(self):
        BoundLogger.reset_defaults()

    def test_fails_on_non_tls(self, logger):
        l = BoundLogger.wrap(logger)
        with pytest.raises(ValueError) as e:
            with tmp_bind(l, x=42):
                pass
        assert e.value.args[0].startswith(
            'tmp_bind works only with loggers whose context class has been '
            'wrapped with wrap_dict.'
        )

    def test_converts_passed_and_yielded_logger(self, logger, OD):
        """
        If the wrapped logger has been created before it was configured,
        the context may be in a wrong class.
        """
        l = BoundLogger.wrap(logger)
        BoundLogger.configure(context_class=OD)
        with tmp_bind(l, x=42) as l2:
            assert l._context == l2._context
            assert l._context.__class__ is l2._context.__class__
            assert "x=42 event='bar'" == l2.msg('bar') == l.msg('bar')
        assert "event='bar'" == l.msg('bar')

    def test_bind(self, logger, OD):
        l = BoundLogger.wrap(logger, context_class=OD)
        l.bind(y=23)
        assert isinstance(l._context, OD)
        with tmp_bind(l, x=42, y='foo'):
            assert 42 == l._context._dict['x']
        assert {'y': 23} == l._context._dict
        with tmp_bind(l, x=42, y='foo'):
            assert 42 == l._context._dict['x']
            assert "y='foo' x=42 event='foo'" == l.msg('foo')
        assert {'y': 23} == l._context._dict
        assert "y=23 event='foo'" == l.msg('foo')


class TestThreadLocalDict(object):
    def test_wrap_returns_distinct_classes(self):
        D1 = wrap_dict(dict)
        D2 = wrap_dict(dict)
        assert D1 != D2
        assert D1 is not D2
        D1.x = 42
        D2.x = 23
        assert D1.x != D2.x

    def test_is_thread_local(self, D):
        class TestThread(threading.Thread):
            def __init__(self, d):
                self._d = d
                threading.Thread.__init__(self)

            def run(self):
                assert 'x' not in self._d._dict
                self._d['x'] = 23
        d = wrap_dict(dict)()
        d['x'] = 42
        t = TestThread(d)
        t.start()
        t.join()
        assert 42 == d._dict['x']

    def test_context_is_global_to_thread(self, D):
        d1 = D({'a': 42})
        d2 = D({'b': 23})
        d3 = D()
        assert {'a': 42, 'b': 23} == d1._dict == d2._dict == d3._dict
        assert d1 == d2 == d3
        D_ = wrap_dict(dict)
        d_ = D_({'a': 42, 'b': 23})
        assert d1 != d_

    def test_init_with_itself_works(self, D):
        d = D({'a': 42})
        assert {'a': 42, 'b': 23} == D(d, b=23)._dict

    def test_iter_works(self, D):
        d = D({'a': 42})
        assert ['a'] == list(iter(d))

    def test_non_dunder_proxy_works(self, D):
        d = D({'a': 42})
        assert 1 == len(d)
        d.clear()
        assert 0 == len(d)

    def test_repr(self, D):
        r = repr(D({'a': 42}))
        assert r.startswith('<WrappedDict-')
        assert r.endswith("({'a': 42})>")
