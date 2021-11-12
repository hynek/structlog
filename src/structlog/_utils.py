# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Generic utilities.
"""

import errno

from typing import Any, Callable


def until_not_interrupted(f: Callable[..., Any], *args: Any, **kw: Any) -> Any:
    """
    Retry until *f* succeeds or an exception that isn't caused by EINTR occurs.

    :param f: A callable like a function.
    :param *args: Positional arguments for *f*.
    :param **kw: Keyword arguments for *f*.
    """
    while True:
        try:
            return f(*args, **kw)
        except OSError as e:
            if e.args[0] == errno.EINTR:
                continue
            raise
