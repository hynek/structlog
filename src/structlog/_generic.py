# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Generic bound logger that can wrap anything.
"""

from __future__ import absolute_import, division, print_function

from functools import partial

from structlog._base import BoundLoggerBase


class BoundLogger(BoundLoggerBase):
    """
    A generic BoundLogger that can wrap anything.

    Every unknown method will be passed to the wrapped logger.  If that's too
    much magic for you, try :class:`structlog.twisted.BoundLogger` or
    :class:`structlog.twisted.BoundLogger` which also take advantage of
    knowing the wrapped class which generally results in better performance.

    Not intended to be instantiated by yourself.  See
    :func:`~structlog.wrap_logger` and :func:`~structlog.get_logger`.
    """
    def __getattr__(self, method_name):
        """
        If not done so yet, wrap the desired logger method & cache the result.
        """
        wrapped = partial(self._proxy_to_logger, method_name)
        setattr(self, method_name, wrapped)
        return wrapped
