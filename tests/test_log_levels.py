# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import logging
import pickle

import pytest

from structlog import make_filtering_bound_logger
from structlog._log_levels import _LEVEL_TO_NAME
from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
    merge_contextvars,
)
from structlog.testing import CapturingLogger


@pytest.fixture(name="cl")
def fixture_cl():
    return CapturingLogger()


@pytest.fixture(name="bl")
def fixture_bl(cl):
    return make_filtering_bound_logger(logging.INFO)(cl, [], {})


class TestFilteringLogger:
    def test_exact_level(self, bl, cl):
        """
        if log level is exactly the min_level, log.
        """
        bl.info("yep")

        assert [("info", (), {"event": "yep"})] == cl.calls

    async def test_async_exact_level(self, bl, cl):
        """
        if log level is exactly the min_level, log.
        """
        await bl.ainfo("yep")

        assert [("info", (), {"event": "yep"})] == cl.calls

    def test_one_below(self, bl, cl):
        """
        if log level is below the min_level, don't log.
        """
        bl.debug("nope")

        assert [] == cl.calls

    async def test_async_one_below(self, bl, cl):
        """
        if log level is below the min_level, don't log.
        """
        await bl.adebug("nope")

        assert [] == cl.calls

    def test_log_exact_level(self, bl, cl):
        """
        if log level is exactly the min_level, log.
        """
        bl.log(logging.INFO, "yep")

        assert [("info", (), {"event": "yep"})] == cl.calls

    async def test_alog_exact_level(self, bl, cl):
        """
        if log level is exactly the min_level, log.
        """
        await bl.alog(logging.INFO, "yep")

        assert [("info", (), {"event": "yep"})] == cl.calls

    def test_log_one_below(self, bl, cl):
        """
        if log level is below the min_level, don't log.
        """
        bl.log(logging.DEBUG, "nope")

        assert [] == cl.calls

    async def test_alog_one_below(self, bl, cl):
        """
        if log level is below the min_level, don't log.
        """
        await bl.alog(logging.DEBUG, "nope")

        assert [] == cl.calls

    def test_filter_bound_below_missing_event_string(self, bl):
        """
        Missing event arg causes exception below min_level.
        """
        with pytest.raises(TypeError) as exc_info:
            bl.debug(missing="event string!")
        assert exc_info.type is TypeError

        message = "missing 1 required positional argument: 'event'"
        assert message in exc_info.value.args[0]

    def test_filter_bound_exact_missing_event_string(self, bl):
        """
        Missing event arg causes exception even at min_level.
        """
        with pytest.raises(TypeError) as exc_info:
            bl.info(missing="event string!")
        assert exc_info.type is TypeError

        message = "missing 1 required positional argument: 'event'"
        assert message in exc_info.value.args[0]

    def test_exception(self, bl, cl):
        """
        exception ensures that exc_info is set to True, unless it's already
        set.
        """
        bl.exception("boom")

        assert [("error", (), {"event": "boom", "exc_info": True})] == cl.calls

    async def test_async_exception(self, bl, cl):
        """
        exception ensures that exc_info is set to True, unless it's already
        set.
        """
        await bl.aexception("boom")

        assert [("error", (), {"event": "boom", "exc_info": True})] == cl.calls

    def test_exception_passed(self, bl, cl):
        """
        exception if exc_info has a value, exception doesn't tamper with it.
        """
        bl.exception("boom", exc_info=42)

        assert [("error", (), {"event": "boom", "exc_info": 42})] == cl.calls

    async def test_async_exception_passed(self, bl, cl):
        """
        exception if exc_info has a value, exception doesn't tamper with it.
        """
        await bl.aexception("boom", exc_info=42)

        assert [("error", (), {"event": "boom", "exc_info": 42})] == cl.calls

    @pytest.mark.parametrize("level", tuple(_LEVEL_TO_NAME.keys()))
    def test_pickle(self, level):
        """
        FilteringBoundLogger are pickleable.
        """
        bl = make_filtering_bound_logger(level)

        assert bl == pickle.loads(pickle.dumps(bl))

    def test_pos_args(self, bl, cl):
        """
        Positional arguments are used for string interpolation.
        """
        bl.info("hello %s -- %d!", "world", 42)

        assert [("info", (), {"event": "hello world -- 42!"})] == cl.calls

    async def test_async_pos_args(self, bl, cl):
        """
        Positional arguments are used for string interpolation.
        """
        await bl.ainfo("hello %s -- %d!", "world", 42)

        assert [("info", (), {"event": "hello world -- 42!"})] == cl.calls

    @pytest.mark.parametrize(
        "meth,args",
        [
            ("aexception", ("ev",)),
            ("ainfo", ("ev",)),
            ("alog", (logging.INFO, "ev")),
        ],
    )
    async def test_async_contextvars_merged(self, meth, args, cl):
        clear_contextvars()
        bl = make_filtering_bound_logger(logging.INFO)(
            cl, [merge_contextvars], {}
        )
        bind_contextvars(context_included="yep")
        await getattr(bl, meth)(*args)
        assert len(cl.calls) == 1
        assert "context_included" in cl.calls[0].kwargs
