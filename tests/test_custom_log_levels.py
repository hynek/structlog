# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import logging
import re

import pytest

import structlog


@pytest.fixture(autouse=True)
def auto_reset_log_levels():
    yield
    structlog.reset_log_levels()


def test_custom_log_levels_must_be_valid_identifiers():
    """Log levels have to be valid to use as method names."""
    with pytest.raises(
        ValueError, match="Log level names must be valid identifiers"
    ):
        structlog.register_log_level("spam and eggs", 1)


def test_custom_log_levels_cant_be_private():
    """Private and dunder names are forbidden."""
    with pytest.raises(
        ValueError, match="Log level names can't start with '_'"
    ):
        structlog.register_log_level("__init__", 1)


# we don't reproduce the whole list of forbidden names here,
# but at least some of the interesting parts
@pytest.mark.parametrize(
    "levelname", ["notset", "msg", "amsg", "log", "alog", "info", "afatal"]
)
def test_custom_log_levels_cant_match_forbidden_list(levelname):
    """Values in the special deny list are forbidden."""
    with pytest.raises(
        ValueError,
        match=re.escape(
            r"register_log_level() cannot be used with names "
            rf"which are already in use. Got: {levelname!r}"
        ),
    ):
        structlog.register_log_level(levelname, 1)


def test_custom_log_levels_cant_match_existing_levels():
    """No duplicates by value."""
    with pytest.raises(
        ValueError,
        match=re.escape(
            "register_log_level() cannot be used with levels which are "
            f"already in use. Got {logging.INFO!r}, "
            "which maps to 'info'"
        ),
    ):
        structlog.register_log_level("detail", logging.INFO)


def test_custom_log_level_allows_logging_via_named_method(capsys):
    """Logger objects are dynamically updated with registered levels."""
    print_logger = structlog.PrintLogger()
    assert not hasattr(print_logger, "audit")

    structlog.register_log_level("audit", 100)

    assert hasattr(print_logger, "audit")

    print_logger.audit("hello")
    out, err = capsys.readouterr()
    assert "hello\n" == out
    assert "" == err


def test_custom_log_level_can_be_filtered_out(cl):
    """Filtering loggers can act on custom levels."""
    bl = structlog.make_filtering_bound_logger(logging.DEBUG)(cl, [], {})
    structlog.register_log_level("trace", logging.DEBUG - 1)

    bl.trace("ok")
    assert [] == cl.calls

    bl.debug("yeah")
    assert [("debug", (), {"event": "yeah"})] == cl.calls


def test_custom_log_level_can_be_allowed_by_filter(cl):
    """Filtering loggers do not *always* filter out custom levels."""
    bl = structlog.make_filtering_bound_logger(logging.INFO)(cl, [], {})
    structlog.register_log_level("detail", logging.INFO + 1)

    bl.detail("ok")
    assert [("detail", (), {"event": "ok"})] == cl.calls
