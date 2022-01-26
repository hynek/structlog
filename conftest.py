# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import logging

from io import StringIO

import pytest

from structlog._log_levels import _NAME_TO_LEVEL
from structlog.testing import CapturingLogger


try:
    import twisted
except ImportError:
    twisted = None

LOGGER = logging.getLogger()


@pytest.fixture(autouse=True)
def _ensure_logging_framework_not_altered():
    """
    Prevents 'ValueError: I/O operation on closed file.' errors.
    """
    before_handlers = list(LOGGER.handlers)

    yield

    LOGGER.handlers = before_handlers


@pytest.fixture(name="sio")
def _sio():
    """
    A new StringIO instance.
    """
    return StringIO()


@pytest.fixture
def event_dict():
    """
    An example event dictionary with multiple value types w/o the event itself.
    """

    class A:
        def __repr__(self):
            return r"<A(\o/)>"

    return {"a": A(), "b": [3, 4], "x": 7, "y": "test", "z": (1, 2)}


@pytest.fixture(
    name="stdlib_log_method",
    params=[m for m in _NAME_TO_LEVEL if m != "notset"],
)
def _stdlib_log_methods(request):
    return request.param


@pytest.fixture(name="cl")
def _cl():
    return CapturingLogger()


collect_ignore = []
if twisted is None:
    collect_ignore.append("tests/test_twisted.py")
