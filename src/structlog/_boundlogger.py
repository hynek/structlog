# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
The BoundLogger helper providing :mod:`logging` compatibility.

See also :doc:`structlog's standard library support <standard-library>`.
"""

from __future__ import annotations

import logging

from typing import Any

from ._base import BoundLoggerBase
from ._log_levels import _LEVEL_TO_NAME
from .typing import ExcInfo


class BoundLogger(BoundLoggerBase):
    """
    Python Standard Library version of `structlog.BoundLogger`.

    Works exactly like the generic one except that it takes advantage of
    knowing the logging methods in advance.

    Use it like::

        structlog.configure(
            wrapper_class=structlog.stdlib.BoundLogger,
        )

    It also contains a bunch of properties that pass-through to the wrapped
    `logging.Logger` which should make it work as a drop-in replacement.
    """

    _logger: logging.Logger

    def bind(self, **new_values: Any) -> BoundLogger:
        """
        Return a new logger with *new_values* added to the existing ones.
        """
        return super().bind(**new_values)  # type: ignore[return-value]

    def unbind(self, *keys: str) -> BoundLogger:
        """
        Return a new logger with *keys* removed from the context.

        :raises KeyError: If the key is not part of the context.
        """
        return super().unbind(*keys)  # type: ignore[return-value]

    def try_unbind(self, *keys: str) -> BoundLogger:
        """
        Like :meth:`unbind`, but best effort: missing keys are ignored.

        .. versionadded:: 18.2.0
        """
        return super().try_unbind(*keys)  # type: ignore[return-value]

    def new(self, **new_values: Any) -> BoundLogger:
        """
        Clear context and binds *initial_values* using `bind`.

        Only necessary with dict implementations that keep global state like
        those wrapped by `structlog.threadlocal.wrap_dict` when threads
        are re-used.
        """
        return super().new(**new_values)  # type: ignore[return-value]

    def debug(self, event: str | None = None, *args: Any, **kw: Any) -> Any:
        """
        Process event and call `logging.Logger.debug` with the result.
        """
        return self._proxy_to_logger("debug", event, *args, **kw)

    def info(self, event: str | None = None, *args: Any, **kw: Any) -> Any:
        """
        Process event and call `logging.Logger.info` with the result.
        """
        return self._proxy_to_logger("info", event, *args, **kw)

    def warning(self, event: str | None = None, *args: Any, **kw: Any) -> Any:
        """
        Process event and call `logging.Logger.warning` with the result.
        """
        return self._proxy_to_logger("warning", event, *args, **kw)

    warn = warning

    def error(self, event: str | None = None, *args: Any, **kw: Any) -> Any:
        """
        Process event and call `logging.Logger.error` with the result.
        """
        return self._proxy_to_logger("error", event, *args, **kw)

    def critical(self, event: str | None = None, *args: Any, **kw: Any) -> Any:
        """
        Process event and call `logging.Logger.critical` with the result.
        """
        return self._proxy_to_logger("critical", event, *args, **kw)

    def exception(
        self, event: str | None = None, *args: Any, **kw: Any
    ) -> Any:
        """
        Process event and call `logging.Logger.error` with the result,
        after setting ``exc_info`` to `True`.
        """
        kw.setdefault("exc_info", True)

        return self.error(event, *args, **kw)

    def log(
        self, level: int, event: str | None = None, *args: Any, **kw: Any
    ) -> Any:
        """
        Process *event* and call the appropriate logging method depending on
        *level*.
        """
        return self._proxy_to_logger(_LEVEL_TO_NAME[level], event, *args, **kw)

    fatal = critical

    def _proxy_to_logger(
        self,
        method_name: str,
        event: str | None = None,
        *event_args: str,
        **event_kw: Any,
    ) -> Any:
        """
        Propagate a method call to the wrapped logger.

        This is the same as the superclass implementation, except that
        it also preserves positional arguments in the ``event_dict`` so
        that the stdlib's support for format strings can be used.
        """
        if event_args:
            event_kw["positional_args"] = event_args

        return super()._proxy_to_logger(method_name, event=event, **event_kw)

    # Pass-through attributes and methods to mimic the stdlib's logger
    # interface.

    @property
    def name(self) -> str:
        """
        Returns :attr:`logging.Logger.name`
        """
        return self._logger.name

    @property
    def level(self) -> int:
        """
        Returns :attr:`logging.Logger.level`
        """
        return self._logger.level

    @property
    def parent(self) -> Any:
        """
        Returns :attr:`logging.Logger.parent`
        """
        return self._logger.parent

    @property
    def propagate(self) -> bool:
        """
        Returns :attr:`logging.Logger.propagate`
        """
        return self._logger.propagate

    @property
    def handlers(self) -> Any:
        """
        Returns :attr:`logging.Logger.handlers`
        """
        return self._logger.handlers

    @property
    def disabled(self) -> int:
        """
        Returns :attr:`logging.Logger.disabled`
        """
        return self._logger.disabled

    def setLevel(self, level: int) -> None:
        """
        Calls :meth:`logging.Logger.setLevel` with unmodified arguments.
        """
        self._logger.setLevel(level)

    def findCaller(
        self, stack_info: bool = False
    ) -> tuple[str, int, str, str | None]:
        """
        Calls :meth:`logging.Logger.findCaller` with unmodified arguments.
        """
        return self._logger.findCaller(stack_info=stack_info)

    def makeRecord(
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: str,
        args: tuple[Any, ...],
        exc_info: ExcInfo,
        func: str | None = None,
        extra: Any = None,
    ) -> logging.LogRecord:
        """
        Calls :meth:`logging.Logger.makeRecord` with unmodified arguments.
        """
        return self._logger.makeRecord(
            name, level, fn, lno, msg, args, exc_info, func=func, extra=extra
        )

    def handle(self, record: logging.LogRecord) -> None:
        """
        Calls :meth:`logging.Logger.handle` with unmodified arguments.
        """
        self._logger.handle(record)

    def addHandler(self, hdlr: logging.Handler) -> None:
        """
        Calls :meth:`logging.Logger.addHandler` with unmodified arguments.
        """
        self._logger.addHandler(hdlr)

    def removeHandler(self, hdlr: logging.Handler) -> None:
        """
        Calls :meth:`logging.Logger.removeHandler` with unmodified arguments.
        """
        self._logger.removeHandler(hdlr)

    def hasHandlers(self) -> bool:
        """
        Calls :meth:`logging.Logger.hasHandlers` with unmodified arguments.

        Exists only in Python 3.
        """
        return self._logger.hasHandlers()

    def callHandlers(self, record: logging.LogRecord) -> None:
        """
        Calls :meth:`logging.Logger.callHandlers` with unmodified arguments.
        """
        self._logger.callHandlers(record)

    def getEffectiveLevel(self) -> int:
        """
        Calls :meth:`logging.Logger.getEffectiveLevel` with unmodified
        arguments.
        """
        return self._logger.getEffectiveLevel()

    def isEnabledFor(self, level: int) -> bool:
        """
        Calls :meth:`logging.Logger.isEnabledFor` with unmodified arguments.
        """
        return self._logger.isEnabledFor(level)

    def getChild(self, suffix: str) -> logging.Logger:
        """
        Calls :meth:`logging.Logger.getChild` with unmodified arguments.
        """
        return self._logger.getChild(suffix)

