# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import pytest

from structlog import get_config, get_logger, reset_defaults, testing
from structlog.testing import (
    CapturedCall,
    CapturingLogger,
    CapturingLoggerFactory,
    LogCapture,
    ReturnLogger,
    ReturnLoggerFactory,
)


class TestCaptureLogs:
    @classmethod
    def teardown_class(cls):
        reset_defaults()

    def test_captures_logs(self):
        """
        Log entries are captured and retain their structure.
        """
        with testing.capture_logs() as logs:
            get_logger().bind(x="y").info("hello", answer=42)
            get_logger().bind(a="b").info("goodbye", foo={"bar": "baz"})
        assert [
            {"event": "hello", "log_level": "info", "x": "y", "answer": 42},
            {
                "a": "b",
                "event": "goodbye",
                "log_level": "info",
                "foo": {"bar": "baz"},
            },
        ] == logs

    def get_active_procs(self):
        return get_config()["processors"]

    def test_restores_processors_on_success(self):
        """
        Processors are patched within the contextmanager and restored on
        exit.
        """
        orig_procs = self.get_active_procs()
        assert len(orig_procs) > 1

        with testing.capture_logs():
            modified_procs = self.get_active_procs()
            assert len(modified_procs) == 1
            assert isinstance(modified_procs[0], LogCapture)

        restored_procs = self.get_active_procs()
        assert orig_procs is restored_procs
        assert len(restored_procs) > 1

    def test_restores_processors_on_error(self):
        """
        Processors are restored even on errors.
        """
        orig_procs = self.get_active_procs()

        with pytest.raises(NotImplementedError):
            with testing.capture_logs():
                raise NotImplementedError("from test")

        assert orig_procs is self.get_active_procs()

    def test_captures_bound_logers(self):
        """
        Even logs from already bound loggers are captured and their processors
        restored on exit.
        """
        logger = get_logger("bound").bind(foo="bar")
        logger.info("ensure logger is bound")

        with testing.capture_logs() as logs:
            logger.info("hello", answer=42)

        assert logs == [
            {
                "event": "hello",
                "answer": 42,
                "foo": "bar",
                "log_level": "info",
            }
        ]


class TestReturnLogger:
    # @pytest.mark.parametrize("method", stdlib_log_methods)
    def test_stdlib_methods_support(self, stdlib_log_method):
        """
        ReturnLogger implements methods of stdlib loggers.
        """
        v = getattr(ReturnLogger(), stdlib_log_method)("hello")

        assert "hello" == v

    def test_return_logger(self):
        """
        Return logger returns exactly what's sent in.
        """
        obj = ["hello"]

        assert obj is ReturnLogger().msg(obj)


class TestReturnLoggerFactory:
    def test_builds_returnloggers(self):
        """
        Factory returns ReturnLoggers.
        """
        f = ReturnLoggerFactory()

        assert isinstance(f(), ReturnLogger)

    def test_caches(self):
        """
        There's no need to have several loggers so we return the same one on
        each call.
        """
        f = ReturnLoggerFactory()

        assert f() is f()

    def test_ignores_args(self):
        """
        ReturnLogger doesn't take positional arguments.  If any are passed to
        the factory, they are not passed to the logger.
        """
        ReturnLoggerFactory()(1, 2, 3)


class TestCapturingLogger:
    def test_factory_caches(self):
        """
        CapturingLoggerFactory returns one CapturingLogger over and over again.
        """
        clf = CapturingLoggerFactory()
        cl1 = clf()
        cl2 = clf()

        assert cl1 is cl2

    def test_repr(self):
        """
        repr says how many calls there were.
        """
        cl = CapturingLogger()

        cl.info("hi")
        cl.error("yolo")

        assert "<CapturingLogger with 2 call(s)>" == repr(cl)

    def test_captures(self):
        """
        All calls to all names are captured.
        """
        cl = CapturingLogger()

        cl.info("hi", val=42)
        cl.trololo("yolo", foo={"bar": "baz"})

        assert [
            CapturedCall(method_name="info", args=("hi",), kwargs={"val": 42}),
            CapturedCall(
                method_name="trololo",
                args=("yolo",),
                kwargs={"foo": {"bar": "baz"}},
            ),
        ] == cl.calls
