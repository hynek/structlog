# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Shared test utilities.
"""

from structlog._log_levels import _NAME_TO_LEVEL


stdlib_log_methods = [m for m in _NAME_TO_LEVEL if m != "notset"]
