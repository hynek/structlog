# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Shared test utilities.
"""

from unittest.mock import Mock, seal

from structlog._log_levels import NAME_TO_LEVEL


stdlib_log_methods = [m for m in NAME_TO_LEVEL if m != "notset"]


class CustomError(Exception):
    """
    Custom exception for testing purposes.
    """


def stub(**kwargs):
    """
    Create a restrictive mock that prevents new attributes after creation.
    Similar to pretend.stub().
    """
    m = Mock(**kwargs)
    seal(m)

    return m


def raiser(exception):
    """
    Create a mock that raises the given exception when called.
    """
    return Mock(side_effect=exception)


def call_recorder(func):
    """
    Create a mock that records calls while executing func.
    """
    return Mock(side_effect=func)
