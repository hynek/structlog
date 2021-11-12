# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import pickle

import pytest

from structlog._config import _CONFIG
from structlog._generic import BoundLogger
from structlog.testing import ReturnLogger


class TestLogger:
    def log(self, msg):
        return "log", msg

    def gol(self, msg):
        return "gol", msg


class TestGenericBoundLogger:
    def test_caches(self):
        """
        __getattr__() gets called only once per logger method.
        """
        b = BoundLogger(
            ReturnLogger(),
            _CONFIG.default_processors,
            _CONFIG.default_context_class(),
        )

        assert "msg" not in b.__dict__

        b.msg("foo")

        assert "msg" in b.__dict__

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

        assert "log", "foo" == b.log("foo")
        assert "gol", "bar" == b.gol("bar")

    @pytest.mark.parametrize("proto", range(pickle.HIGHEST_PROTOCOL + 1))
    def test_pickle(self, proto):
        """
        Can be pickled and unpickled.

        Works only on Python 3: TypeError: can't pickle instancemethod objects
        """
        b = BoundLogger(
            ReturnLogger(),
            _CONFIG.default_processors,
            _CONFIG.default_context_class(),
        ).bind(x=1)

        assert b.info("hi") == pickle.loads(pickle.dumps(b, proto)).info("hi")

    def test_deepcopy(self):
        """
        __getattr__ returns None for '__deepcopy__'
        """
        b = BoundLogger(
            ReturnLogger(),
            _CONFIG.default_processors,
            _CONFIG.default_context_class(),
        )

        assert b.__deepcopy__ is None
