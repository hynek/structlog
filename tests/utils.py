# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Shared test utilities.
"""
import sys
from types import FrameType

from structlog._log_levels import _NAME_TO_LEVEL


stdlib_log_methods = [m for m in _NAME_TO_LEVEL if m != "notset"]


_REAL_GETFRAME = sys._getframe


def mock_getframe(__depth: int = 0) -> FrameType:
    real_frame: FrameType = _REAL_GETFRAME(__depth)
    return real_frame
