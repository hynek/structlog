# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Generic bound logger that can wrap anything.
"""
from functools import partial
from typing import Any, Dict

from structlog._base import BoundLoggerBase


class BoundLogger(BoundLoggerBase):
    """
    A generic BoundLogger that can wrap anything.

    Every unknown method will be passed to the wrapped *logger*. If that's too
    much magic for you, try `structlog.stdlib.BoundLogger` or
    `structlog.twisted.BoundLogger` which also take advantage of knowing the
    wrapped class which generally results in better performance.

    Not intended to be instantiated by yourself.  See
    :func:`~structlog.wrap_logger` and :func:`~structlog.get_logger`.
    """

    def __getattr__(self, method_name: str) -> Any:
        """
        If not done so yet, wrap the desired logger method & cache the result.
        """
        if method_name == "__deepcopy__":
            return None

        wrapped = partial(self._proxy_to_logger, method_name)
        setattr(self, method_name, wrapped)

        return wrapped

    def __getstate__(self) -> Dict[str, Any]:
        """
        Our __getattr__ magic makes this necessary.
        """
        return self.__dict__

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """
        Our __getattr__ magic makes this necessary.
        """
        for k, v in state.items():
            setattr(self, k, v)
