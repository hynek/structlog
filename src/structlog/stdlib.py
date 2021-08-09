# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Processors and helpers specific to the :mod:`logging` module from the `Python
standard library <https://docs.python.org/>`_.

See also :doc:`structlog's standard library support <standard-library>`.
"""

import asyncio
import logging
import sys

from functools import partial
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
)

from ._base import BoundLoggerBase
from ._config import get_logger as _generic_get_logger
from ._frames import _find_first_app_frame_and_name, _format_stack
from ._log_levels import _LEVEL_TO_NAME, _NAME_TO_LEVEL, add_log_level
from .exceptions import DropEvent
from .types import Context, EventDict, ExcInfo, Processor, WrappedLogger


try:
    import contextvars
except ImportError:
    contextvars = None  # type: ignore


__all__ = [
    "add_log_level_number",
    "add_log_level",
    "add_logger_name",
    "BoundLogger",
    "filter_by_level",
    "get_logger",
    "LoggerFactory",
    "PositionalArgumentsFormatter",
    "ProcessorFormatter",
    "render_to_log_kwargs",
]


_SENTINEL = object()


class _FixedFindCallerLogger(logging.Logger):
    """
    Change the behavior of `logging.Logger.findCaller` to cope with
    ``structlog``'s extra frames.
    """

    def findCaller(
        self, stack_info: bool = False, stacklevel: int = 1
    ) -> Tuple[str, int, str, Optional[str]]:
        """
        Finds the first caller frame outside of structlog so that the caller
        info is populated for wrapping stdlib.

        This logger gets set as the default one when using LoggerFactory.
        """
        sinfo: Optional[str]
        f, name = _find_first_app_frame_and_name(["logging"])
        if stack_info:
            sinfo = _format_stack(f)
        else:
            sinfo = None

        return f.f_code.co_filename, f.f_lineno, f.f_code.co_name, sinfo


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

    def bind(self, **new_values: Any) -> "BoundLogger":
        """
        Return a new logger with *new_values* added to the existing ones.
        """
        return super().bind(**new_values)  # type: ignore

    def unbind(self, *keys: str) -> "BoundLogger":
        """
        Return a new logger with *keys* removed from the context.

        :raises KeyError: If the key is not part of the context.
        """
        return super().unbind(*keys)  # type: ignore

    def try_unbind(self, *keys: str) -> "BoundLogger":
        """
        Like :meth:`unbind`, but best effort: missing keys are ignored.

        .. versionadded:: 18.2.0
        """
        return super().try_unbind(*keys)  # type: ignore

    def new(self, **new_values: Any) -> "BoundLogger":
        """
        Clear context and binds *initial_values* using `bind`.

        Only necessary with dict implementations that keep global state like
        those wrapped by `structlog.threadlocal.wrap_dict` when threads
        are re-used.
        """
        return super().new(**new_values)  # type: ignore

    def debug(self, event: Optional[str] = None, *args: Any, **kw: Any) -> Any:
        """
        Process event and call `logging.Logger.debug` with the result.
        """
        return self._proxy_to_logger("debug", event, *args, **kw)

    def info(self, event: Optional[str] = None, *args: Any, **kw: Any) -> Any:
        """
        Process event and call `logging.Logger.info` with the result.
        """
        return self._proxy_to_logger("info", event, *args, **kw)

    def warning(
        self, event: Optional[str] = None, *args: Any, **kw: Any
    ) -> Any:
        """
        Process event and call `logging.Logger.warning` with the result.
        """
        return self._proxy_to_logger("warning", event, *args, **kw)

    warn = warning

    def error(self, event: Optional[str] = None, *args: Any, **kw: Any) -> Any:
        """
        Process event and call `logging.Logger.error` with the result.
        """
        return self._proxy_to_logger("error", event, *args, **kw)

    def critical(
        self, event: Optional[str] = None, *args: Any, **kw: Any
    ) -> Any:
        """
        Process event and call `logging.Logger.critical` with the result.
        """
        return self._proxy_to_logger("critical", event, *args, **kw)

    def exception(
        self, event: Optional[str] = None, *args: Any, **kw: Any
    ) -> Any:
        """
        Process event and call `logging.Logger.error` with the result,
        after setting ``exc_info`` to `True`.
        """
        kw.setdefault("exc_info", True)

        return self.error(event, *args, **kw)

    def log(
        self, level: int, event: Optional[str] = None, *args: Any, **kw: Any
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
        event: Optional[str] = None,
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

    #
    # Pass-through attributes and methods to mimick the stdlib's logger
    # interface.
    #

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
    ) -> Tuple[str, int, str, Optional[str]]:
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
        args: Tuple[Any, ...],
        exc_info: ExcInfo,
        func: Optional[str] = None,
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


def get_logger(*args: Any, **initial_values: Any) -> BoundLogger:
    """
    Only calls `structlog.get_logger`, but has the correct type hints.

    .. warning::

       Does **not** check whether you've configured ``structlog`` correctly!

       See :doc:`standard-library` for details.

    .. versionadded:: 20.2.0
    """
    return _generic_get_logger(*args, **initial_values)


class AsyncBoundLogger:
    """
    Wraps a `BoundLogger` & exposes its logging methods as ``async`` versions.

    Instead of blocking the program, they are run asynchronously in a thread
    pool executor.

    This means more computational overhead per log call. But it also means that
    the processor chain (e.g. JSON serialization) and I/O won't block your
    whole application.

    Only available for Python 3.7 and later.

    :ivar structlog.stdlib.BoundLogger sync_bl: The wrapped synchronous logger.
       It is useful to be able to log synchronously occasionally.

    .. versionadded:: 20.2.0
    .. versionchanged:: 20.2.0 fix _dispatch_to_sync contextvars usage
    """

    __slots__ = ["sync_bl", "_loop"]

    sync_bl: BoundLogger

    # Blantant lie, we use a property for _context. Need this for Protocol
    # though.
    _context: Context

    _executor = None
    _bound_logger_factory = BoundLogger

    def __init__(
        self,
        logger: logging.Logger,
        processors: Iterable[Processor],
        context: Context,
        *,
        # Only as an optimization for binding!
        _sync_bl: Any = None,  # *vroom vroom* over purity.
        _loop: Any = None,
    ):
        if _sync_bl:
            self.sync_bl = _sync_bl
            self._loop = _loop

            return

        self.sync_bl = self._bound_logger_factory(
            logger=logger, processors=processors, context=context
        )
        self._loop = asyncio.get_running_loop()

    # We have to ignore the type because we've already declared it to ensure
    # we're a BindableLogger.
    # Instances would've been correctly recognized as such, however the class
    # not and we need the class in `structlog.configure()`.
    @property  # type: ignore
    def _context(self) -> Context:
        return self.sync_bl._context

    def bind(self, **new_values: Any) -> "AsyncBoundLogger":
        return AsyncBoundLogger(
            # logger, processors and context are within sync_bl. These
            # arguments are ignored if _sync_bl is passed. *vroom vroom* over
            # purity.
            logger=None,  # type: ignore
            processors=(),
            context={},
            _sync_bl=self.sync_bl.bind(**new_values),
            _loop=self._loop,
        )

    def new(self, **new_values: Any) -> "AsyncBoundLogger":
        return AsyncBoundLogger(
            # c.f. comment in bind
            logger=None,  # type: ignore
            processors=(),
            context={},
            _sync_bl=self.sync_bl.new(**new_values),
            _loop=self._loop,
        )

    def unbind(self, *keys: str) -> "AsyncBoundLogger":
        return AsyncBoundLogger(
            # c.f. comment in bind
            logger=None,  # type: ignore
            processors=(),
            context={},
            _sync_bl=self.sync_bl.unbind(*keys),
            _loop=self._loop,
        )

    def try_unbind(self, *keys: str) -> "AsyncBoundLogger":
        return AsyncBoundLogger(
            # c.f. comment in bind
            logger=None,  # type: ignore
            processors=(),
            context={},
            _sync_bl=self.sync_bl.try_unbind(*keys),
            _loop=self._loop,
        )

    async def _dispatch_to_sync(
        self,
        meth: Callable[..., Any],
        event: str,
        args: Tuple[Any, ...],
        kw: Dict[str, Any],
    ) -> None:
        """
        Merge contextvars and log using the sync logger in a thread pool.
        """
        ctx = contextvars.copy_context()

        await self._loop.run_in_executor(
            self._executor, partial(ctx.run, partial(meth, event, *args, **kw))
        )

    async def debug(self, event: str, *args: Any, **kw: Any) -> None:
        await self._dispatch_to_sync(self.sync_bl.debug, event, args, kw)

    async def info(self, event: str, *args: Any, **kw: Any) -> None:
        await self._dispatch_to_sync(self.sync_bl.info, event, args, kw)

    async def warning(self, event: str, *args: Any, **kw: Any) -> None:
        await self._dispatch_to_sync(self.sync_bl.warning, event, args, kw)

    warn = warning

    async def error(self, event: str, *args: Any, **kw: Any) -> None:
        await self._dispatch_to_sync(self.sync_bl.error, event, args, kw)

    async def critical(self, event: str, *args: Any, **kw: Any) -> None:
        await self._dispatch_to_sync(self.sync_bl.critical, event, args, kw)

    fatal = critical

    async def exception(self, event: str, *args: Any, **kw: Any) -> None:
        # To make `log.exception("foo") work, we have to check if the user
        # passed an explicit exc_info and if not, supply our own.
        ei = kw.pop("exc_info", None)
        if ei is None and kw.get("exception") is None:
            ei = sys.exc_info()

        kw["exc_info"] = ei

        await self._dispatch_to_sync(self.sync_bl.exception, event, args, kw)

    async def log(self, level: Any, event: str, *args: Any, **kw: Any) -> None:
        await self._dispatch_to_sync(
            partial(self.sync_bl.log, level), event, args, kw
        )


class LoggerFactory:
    """
    Build a standard library logger when an *instance* is called.

    Sets a custom logger using :func:`logging.setLoggerClass` so variables in
    log format are expanded properly.

    >>> from structlog import configure
    >>> from structlog.stdlib import LoggerFactory
    >>> configure(logger_factory=LoggerFactory())

    :param ignore_frame_names: When guessing the name of a logger, skip frames
        whose names *start* with one of these.  For example, in pyramid
        applications you'll want to set it to
        ``["venusian", "pyramid.config"]``.
    """

    def __init__(self, ignore_frame_names: Optional[List[str]] = None):
        self._ignore = ignore_frame_names
        logging.setLoggerClass(_FixedFindCallerLogger)

    def __call__(self, *args: Any) -> logging.Logger:
        """
        Deduce the caller's module name and create a stdlib logger.

        If an optional argument is passed, it will be used as the logger name
        instead of guesswork.  This optional argument would be passed from the
        :func:`structlog.get_logger` call.  For example
        ``structlog.get_logger("foo")`` would cause this method to be called
        with ``"foo"`` as its first positional argument.

        .. versionchanged:: 0.4.0
            Added support for optional positional arguments.  Using the first
            one for naming the constructed logger.
        """
        if args:
            return logging.getLogger(args[0])

        # We skip all frames that originate from within structlog or one of the
        # configured names.
        _, name = _find_first_app_frame_and_name(self._ignore)

        return logging.getLogger(name)


class PositionalArgumentsFormatter:
    """
    Apply stdlib-like string formatting to the ``event`` key.

    If the ``positional_args`` key in the event dict is set, it must
    contain a tuple that is used for formatting (using the ``%s`` string
    formatting operator) of the value from the ``event`` key.  This works
    in the same way as the stdlib handles arguments to the various log
    methods: if the tuple contains only a single `dict` argument it is
    used for keyword placeholders in the ``event`` string, otherwise it
    will be used for positional placeholders.

    ``positional_args`` is populated by `structlog.stdlib.BoundLogger` or
    can be set manually.

    The *remove_positional_args* flag can be set to `False` to keep the
    ``positional_args`` key in the event dict; by default it will be
    removed from the event dict after formatting a message.
    """

    def __init__(self, remove_positional_args: bool = True) -> None:
        self.remove_positional_args = remove_positional_args

    def __call__(
        self, _: WrappedLogger, __: str, event_dict: EventDict
    ) -> EventDict:
        args = event_dict.get("positional_args")

        # Mimick the formatting behaviour of the stdlib's logging
        # module, which accepts both positional arguments and a single
        # dict argument. The "single dict" check is the same one as the
        # stdlib's logging module performs in LogRecord.__init__().
        if args:
            if len(args) == 1 and isinstance(args[0], dict) and args[0]:
                args = args[0]

            event_dict["event"] = event_dict["event"] % args

        if self.remove_positional_args and args is not None:
            del event_dict["positional_args"]

        return event_dict


def filter_by_level(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Check whether logging is configured to accept messages from this log level.

    Should be the first processor if stdlib's filtering by level is used so
    possibly expensive processors like exception formatters are avoided in the
    first place.

    >>> import logging
    >>> from structlog.stdlib import filter_by_level
    >>> logging.basicConfig(level=logging.WARN)
    >>> logger = logging.getLogger()
    >>> filter_by_level(logger, 'warn', {})
    {}
    >>> filter_by_level(logger, 'debug', {})
    Traceback (most recent call last):
    ...
    DropEvent
    """
    if logger.isEnabledFor(_NAME_TO_LEVEL[method_name]):
        return event_dict
    else:
        raise DropEvent


def add_log_level_number(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Add the log level number to the event dict.

    Log level numbers map to the log level names. The Python stdlib uses them
    for filtering logic. This adds the same numbers so users can leverage
    similar filtering. Compare::

       level in ("warning", "error", "critical")
       level_number >= 30

    The mapping of names to numbers is in
    ``structlog.stdlib._log_levels._NAME_TO_LEVEL``.

    .. versionadded:: 18.2.0
    """
    event_dict["level_number"] = _NAME_TO_LEVEL[method_name]

    return event_dict


def add_logger_name(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Add the logger name to the event dict.
    """
    record = event_dict.get("_record")
    if record is None:
        event_dict["logger"] = logger.name
    else:
        event_dict["logger"] = record.name
    return event_dict


def render_to_log_kwargs(
    _: logging.Logger, __: str, event_dict: EventDict
) -> EventDict:
    """
    Render ``event_dict`` into keyword arguments for `logging.log`.

    The ``event`` field is translated into ``msg`` and the rest of the
    *event_dict* is added as ``extra``.

    This allows you to defer formatting to `logging`.

    .. versionadded:: 17.1.0
    """
    return {"msg": event_dict.pop("event"), "extra": event_dict}


class ProcessorFormatter(logging.Formatter):
    r"""
    Call ``structlog`` processors on :`logging.LogRecord`\ s.

    This `logging.Formatter` allows to configure :mod:`logging` to call
    *processor* on ``structlog``-borne log entries (origin is determined solely
    on the fact whether the ``msg`` field on the `logging.LogRecord` is
    a dict or not).

    This allows for two interesting use cases:

    #. You can format non-``structlog`` log entries.
    #. You can multiplex log records into multiple `logging.Handler`\ s.

    Please refer to :doc:`standard-library` for examples.

    :param processor: A ``structlog`` processor.
    :param foreign_pre_chain:
        If not `None`, it is used as an iterable of processors that is applied
        to non-``structlog`` log entries before *processor*.  If `None`,
        formatting is left to :mod:`logging`. (default: `None`)
    :param keep_exc_info: ``exc_info`` on `logging.LogRecord`\ s is
        added to the ``event_dict`` and removed afterwards. Set this to
        ``True`` to keep it on the `logging.LogRecord`. (default: False)
    :param keep_stack_info: Same as *keep_exc_info* except for Python 3's
        ``stack_info``. (default: False)
    :param logger: Logger which we want to push through the ``structlog``
        processor chain. This parameter is necessary for some of the
        processors like `filter_by_level`. (default: None)
    :param pass_foreign_args: If True, pass a foreign log record's
        ``args`` attribute to the ``event_dict`` under ``positional_args`` key.
        (default: False)

    .. versionadded:: 17.1.0
    .. versionadded:: 17.2.0 *keep_exc_info* and *keep_stack_info*
    .. versionadded:: 19.2.0 *logger*
    .. versionadded:: 19.2.0 *pass_foreign_args*
    """

    def __init__(
        self,
        processor: Processor,
        foreign_pre_chain: Optional[Sequence[Processor]] = None,
        keep_exc_info: bool = False,
        keep_stack_info: bool = False,
        logger: Optional[logging.Logger] = None,
        pass_foreign_args: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        fmt = kwargs.pop("fmt", "%(message)s")
        super().__init__(*args, fmt=fmt, **kwargs)  # type: ignore

        self.processor = processor
        self.foreign_pre_chain = foreign_pre_chain
        self.keep_exc_info = keep_exc_info
        self.keep_stack_info = keep_stack_info
        self.logger = logger
        self.pass_foreign_args = pass_foreign_args

    def format(self, record: logging.LogRecord) -> str:
        """
        Extract ``structlog``'s `event_dict` from ``record.msg`` and format it.

        *record* has been patched by `wrap_for_formatter` first though, so the
         type isn't quite right.
        """
        # Make a shallow copy of the record to let other handlers/formatters
        # process the original one
        record = logging.makeLogRecord(record.__dict__)

        logger = getattr(record, "_logger", _SENTINEL)
        meth_name = getattr(record, "_name", _SENTINEL)

        if logger is not _SENTINEL and meth_name is not _SENTINEL:
            # Both attached by wrap_for_formatter
            if self.logger is not None:
                logger = self.logger
            meth_name = record._name  # type: ignore

            # We need to copy because it's possible that the same record gets
            # processed by multiple logging formatters.  LogRecord.getMessage
            # would transform our dict into a str.
            ed = record.msg.copy()  # type: ignore
        else:
            logger = self.logger
            meth_name = record.levelname.lower()
            ed = {"event": record.getMessage(), "_record": record}

            if self.pass_foreign_args:
                ed["positional_args"] = record.args

            record.args = ()

            # Add stack-related attributes to event_dict and unset them
            # on the record copy so that the base implementation wouldn't
            # append stacktraces to the output.
            if record.exc_info:
                ed["exc_info"] = record.exc_info
            if record.stack_info:
                ed["stack_info"] = record.stack_info

            if not self.keep_exc_info:
                record.exc_text = None
                record.exc_info = None
            if not self.keep_stack_info:
                record.stack_info = None

            # Non-structlog allows to run through a chain to prepare it for the
            # final processor (e.g. adding timestamps and log levels).
            for proc in self.foreign_pre_chain or ():
                ed = proc(logger, meth_name, ed)

            del ed["_record"]

        record.msg = self.processor(logger, meth_name, ed)  # type: ignore

        return super().format(record)

    @staticmethod
    def wrap_for_formatter(
        logger: logging.Logger, name: str, event_dict: EventDict
    ) -> Tuple[Tuple[EventDict], Dict[str, Dict[str, Any]]]:
        """
        Wrap *logger*, *name*, and *event_dict*.

        The result is later unpacked by `ProcessorFormatter` when
        formatting log entries.

        Use this static method as the renderer (i.e. final processor) if you
        want to use `ProcessorFormatter` in your `logging` configuration.
        """
        return (event_dict,), {"extra": {"_logger": logger, "_name": name}}
