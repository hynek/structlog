# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Helper function for testing the deduction of stdlib logger names.

Since the logger factories are called from within structlog._config, they have
to skip a frame.  Calling them here emulates that.
"""

from __future__ import absolute_import, division, print_function


def additional_frame(callable):
    return callable()
