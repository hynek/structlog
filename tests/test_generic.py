# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import absolute_import, division, print_function

from structlog._config import _CONFIG
from structlog._generic import BoundLogger
from structlog._loggers import ReturnLogger


class TestLogger(object):
    def log(self, msg):
        return 'log', msg

    def gol(self, msg):
        return 'gol', msg


class TestGenericBoundLogger(object):
    def test_caches(self):
        """
        __getattr__() gets called only once per logger method.
        """
        b = BoundLogger(
            ReturnLogger(),
            _CONFIG.default_processors,
            _CONFIG.default_context_class(),
        )
        assert 'msg' not in b.__dict__
        b.msg('foo')
        assert 'msg' in b.__dict__

    def test_proxies_anything(self):
        """
        Anything that isn't part of BoundLoggerBase gets proxied to the correct
        wrapped logger methods.
        """
        b = BoundLogger(
            ReturnLogger(),
            _CONFIG.default_processors,
            _CONFIG.default_context_class(),
        )
        assert 'log', 'foo' == b.log('foo')
        assert 'gol', 'bar' == b.gol('bar')
