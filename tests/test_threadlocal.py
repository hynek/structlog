# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import absolute_import, division, print_function

import threading

from collections import OrderedDict

import pytest

from structlog._base import BoundLoggerBase
from structlog._config import wrap_logger
from structlog._loggers import ReturnLogger
from structlog.threadlocal import as_immutable, wrap_dict, tmp_bind

try:
    import greenlet
except ImportError:
    greenlet = None


@pytest.fixture
def D():
    """
    Returns a dict wrapped in _ThreadLocalDictWrapper.
    """
    return wrap_dict(dict)


@pytest.fixture
def log():
    """
    Returns a ReturnLogger with a freshly wrapped OrderedDict.
    """
    return wrap_logger(logger(), context_class=wrap_dict(OrderedDict))


@pytest.fixture
def logger():
    """
    Returns a simple logger stub with a *msg* method that takes one argument
    which gets returned.
    """
    return ReturnLogger()


class TestTmpBind(object):
    def test_bind(self, log):
        """
        tmp_bind does not modify the thread-local state.
        """
        log = log.bind(y=23)
        with tmp_bind(log, x=42, y='foo') as tmp_log:
            assert {
                'y': 'foo', 'x': 42
            } == tmp_log._context._dict == log._context._dict
        assert {'y': 23} == log._context._dict

    def test_bind_exc(self, log):
        """
        tmp_bind cleans up properly on exceptions.
        """
        log = log.bind(y=23)
        with pytest.raises(ValueError):
            with tmp_bind(log, x=42, y='foo') as tmp_log:
                assert {
                           'y': 'foo', 'x': 42
                       } == tmp_log._context._dict == log._context._dict
                raise ValueError
        assert {'y': 23} == log._context._dict


class TestAsImmutable(object):
    def test_does_not_affect_global(self, log):
        """
        A logger from as_mutable is independent from thread local state.
        """
        log = log.new(x=42)
        il = as_immutable(log)
        assert isinstance(il._context, dict)
        il = il.bind(y=23)
        assert {'x': 42, 'y': 23} == il._context
        assert {'x': 42} == log._context._dict

    def test_converts_proxy(self, log):
        """
        as_immutable converts a BoundLoggerLazyProxy into a concrete bound
        logger.
        """
        il = as_immutable(log)
        assert isinstance(il._context, dict)
        assert isinstance(il, BoundLoggerBase)

    def test_idempotency(self, log):
        """
        as_immutable on an as_immutable logger works.
        """
        il = as_immutable(log)
        assert isinstance(as_immutable(il), BoundLoggerBase)


class TestThreadLocalDict(object):
    def test_wrap_returns_distinct_classes(self):
        """
        Each call to wrap_dict returns a distinct new class whose context is
        independent from others.
        """
        D1 = wrap_dict(dict)
        D2 = wrap_dict(dict)
        assert D1 != D2
        assert D1 is not D2
        D1.x = 42
        D2.x = 23
        assert D1.x != D2.x

    @pytest.mark.skipif(greenlet is not None,
                        reason="Don't mix threads and greenlets.")
    def test_is_thread_local(self, D):
        """
        The context is *not* shared between threads.
        """
        class TestThread(threading.Thread):
            def __init__(self, d):
                self._d = d
                threading.Thread.__init__(self)

            def run(self):
                assert 'tl' not in self._d._dict
                self._d['tl'] = 23
        d = wrap_dict(dict)()
        d['tl'] = 42
        t = TestThread(d)
        t.start()
        t.join()
        assert 42 == d._dict['tl']

    def test_context_is_global_to_thread(self, D):
        """
        The context is shared between all instances of a wrapped class.
        """
        d1 = D({'a': 42})
        d2 = D({'b': 23})
        d3 = D()
        assert {'a': 42, 'b': 23} == d1._dict == d2._dict == d3._dict
        assert d1 == d2 == d3
        D_ = wrap_dict(dict)
        d_ = D_({'a': 42, 'b': 23})
        assert d1 != d_

    def test_init_with_itself_works(self, D):
        """
        Initializing with an instance of the wrapped class will use its values.
        """
        d = D({'a': 42})
        assert {'a': 42, 'b': 23} == D(d, b=23)._dict

    def test_iter_works(self, D):
        """
        ___iter__ is proxied to the wrapped class.
        """
        d = D({'a': 42})
        assert ['a'] == list(iter(d))

    def test_non_dunder_proxy_works(self, D):
        """
        Calls to a non-dunder method get proxied to the wrapped class.
        """
        d = D({'a': 42})
        d.clear()
        assert 0 == len(d)

    def test_repr(self, D):
        """
        ___repr__ takes the repr of the wrapped class into account.
        """
        r = repr(D({'a': 42}))
        assert r.startswith('<WrappedDict-')
        assert r.endswith("({'a': 42})>")

    @pytest.mark.skipif(greenlet is None, reason="Needs greenlet.")
    def test_is_greenlet_local(self, D):
        """
        Context is shared between greenlets.
        """
        d = wrap_dict(dict)()
        d['switch'] = 42

        def run():
            assert 'x' not in d._dict
            d['switch'] = 23

        greenlet.greenlet(run).switch()
        assert 42 == d._dict["switch"]

    def test_delattr(self, D):
        """
        ___delattr__ is proxied to the wrapped class.
        """
        d = D()
        d['delattr'] = 42
        assert 42 == d._dict["delattr"]
        del d.__class__._tl.dict_

    def test_delattr_missing(self, D):
        """
        __delattr__ on an inexisting attribute raises AttributeError.
        """
        d = D()
        with pytest.raises(AttributeError) as e:
            d._tl.__delattr__("does_not_exist")
        assert "does_not_exist" == e.value.args[0]

    def test_del(self, D):
        """
        ___del__ is proxied to the wrapped class.
        """
        d = D()
        d["del"] = 13
        assert 13 == d._dict["del"]
        del d["del"]
        assert "del" not in d._dict

    def test_new_class(self, D):
        """
        The context of a new wrapped class is empty.
        """
        assert 0 == len(D())
