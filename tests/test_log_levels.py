# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import logging
import pickle

import pytest

from structlog import make_filtering_bound_logger
from structlog._log_levels import _LEVEL_TO_NAME
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

    def test_one_below(self, bl, cl):
        """
        if log level is exactly the min_level, log.
        """
        bl.debug("nope")

        assert [] == cl.calls

    def test_exception(self, bl, cl):
        """
        exception ensures that exc_info is set to True, unless it's already
        set.
        """
        bl.exception("boom")

        assert [("error", (), {"event": "boom", "exc_info": True})]

    def test_exception_passed(self, bl, cl):
        """
        exception if exc_info has a value, exception doesn't tamper with it.
        """
        bl.exception("boom", exc_info=42)

        assert [("error", (), {"event": "boom", "exc_info": 42})]

    @pytest.mark.parametrize("level", tuple(_LEVEL_TO_NAME.keys()))
    def test_pickle(self, level):
        """
        FilteringBoundLogger are pickleable.
        """
        bl = make_filtering_bound_logger(level)

        assert bl == pickle.loads(pickle.dumps(bl))
