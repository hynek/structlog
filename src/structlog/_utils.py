# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Generic utilities.
"""

from __future__ import absolute_import, division, print_function

import errno


def until_not_interrupted(f, *args, **kw):
    """
    Retry until *f* succeeds or an exception that isn't caused by EINTR occurs.

    :param callable f: A callable like a function.
    :param *args: Positional arguments for *f*.
    :param **kw: Keyword arguments for *f*.
    """
    while True:
        try:
            return f(*args, **kw)
        except (IOError, OSError) as e:
            if e.args[0] == errno.EINTR:
                continue
            raise
