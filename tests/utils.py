# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Shared test utilities.
"""

from structlog._log_levels import NAME_TO_LEVEL


stdlib_log_methods = [m for m in NAME_TO_LEVEL if m != "notset"]


class CustomError(Exception):
    """
    Custom exception for testing purposes.
    """
