# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Processors and helpers specific to the :mod:`logging` module from the `Python
standard library <https://docs.python.org/>`_.

See also :doc:`structlog's standard library support <standard-library>`.
"""

from __future__ import absolute_import, division, print_function

import logging

from six import PY3

from structlog._base import BoundLoggerBase
from structlog._frames import _find_first_app_frame_and_name, _format_stack
from structlog.exceptions import DropEvent


class _FixedFindCallerLogger(logging.Logger):
    """
    Change the behavior of findCaller to cope with structlog's extra frames.
    """

    def findCaller(self, stack_info=False, stacklevel=1):
        """
        Finds the first caller frame outside of structlog so that the caller
        info is populated for wrapping stdlib.
        This logger gets set as the default one when using LoggerFactory.
        """
        f, name = _find_first_app_frame_and_name(["logging"])
        if PY3:
            if stack_info:
                sinfo = _format_stack(f)
            else:
                sinfo = None
            return f.f_code.co_filename, f.f_lineno, f.f_code.co_name, sinfo
        else:
            return f.f_code.co_filename, f.f_lineno, f.f_code.co_name


class BoundLogger(BoundLoggerBase):
    """
    Python Standard Library version of :class:`structlog.BoundLogger`.
    Works exactly like the generic one except that it takes advantage of
    knowing the logging methods in advance.

    Use it like::

        structlog.configure(
            wrapper_class=structlog.stdlib.BoundLogger,
        )

    It also contains a bunch of properties that pass-through to the wrapped
    :class:`logging.Logger` which should make it work as a drop-in
    replacement.
    """

    def debug(self, event=None, *args, **kw):
        """
        Process event and call :meth:`logging.Logger.debug` with the result.
        """
        return self._proxy_to_logger("debug", event, *args, **kw)

    def info(self, event=None, *args, **kw):
        """
        Process event and call :meth:`logging.Logger.info` with the result.
        """
        return self._proxy_to_logger("info", event, *args, **kw)

    def warning(self, event=None, *args, **kw):
        """
        Process event and call :meth:`logging.Logger.warning` with the result.
        """
        return self._proxy_to_logger("warning", event, *args, **kw)

    warn = warning

    def error(self, event=None, *args, **kw):
        """
        Process event and call :meth:`logging.Logger.error` with the result.
        """
        return self._proxy_to_logger("error", event, *args, **kw)

    def critical(self, event=None, *args, **kw):
        """
        Process event and call :meth:`logging.Logger.critical` with the result.
        """
        return self._proxy_to_logger("critical", event, *args, **kw)

    def exception(self, event=None, *args, **kw):
        """
        Process event and call :meth:`logging.Logger.error` with the result,
        after setting ``exc_info`` to `True`.
        """
        kw.setdefault("exc_info", True)
        return self.error(event, *args, **kw)

    def log(self, level, event, *args, **kw):
        """
        Process event and call the appropriate logging method depending on
        `level`.
        """
        return self._proxy_to_logger(_LEVEL_TO_NAME[level], event, *args, **kw)

    fatal = critical

    def _proxy_to_logger(self, method_name, event, *event_args, **event_kw):
        """
        Propagate a method call to the wrapped logger.

        This is the same as the superclass implementation, except that
        it also preserves positional arguments in the `event_dict` so
        that the stdblib's support for format strings can be used.
        """
        if event_args:
            event_kw["positional_args"] = event_args
        return super(BoundLogger, self)._proxy_to_logger(
            method_name, event=event, **event_kw
        )

    #
    # Pass-through attributes and methods to mimick the stdlib's logger
    # interface.
    #

    @property
    def name(self):
        """
        Returns :attr:`logging.Logger.name`
        """
        return self._logger.name

    @property
    def level(self):
        """
        Returns :attr:`logging.Logger.level`
        """
        return self._logger.level

    @property
    def parent(self):
        """
        Returns :attr:`logging.Logger.parent`
        """
        return self._logger.parent

    @property
    def propagate(self):
        """
        Returns :attr:`logging.Logger.propagate`
        """
        return self._logger.propagate

    @property
    def handlers(self):
        """
        Returns :attr:`logging.Logger.handlers`
        """
        return self._logger.handlers

    @property
    def disabled(self):
        """
        Returns :attr:`logging.Logger.disabled`
        """
        return self._logger.disabled

    def setLevel(self, level):
        """
        Calls :meth:`logging.Logger.setLevel` with unmodified arguments.
        """
        self._logger.setLevel(level)

    def findCaller(self, stack_info=False):
        """
        Calls :meth:`logging.Logger.findCaller` with unmodified arguments.
        """
        return self._logger.findCaller(stack_info=stack_info)

    def makeRecord(
        self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None
    ):
        """
        Calls :meth:`logging.Logger.makeRecord` with unmodified arguments.
        """
        return self._logger.makeRecord(
            name, level, fn, lno, msg, args, exc_info, func=func, extra=extra
        )

    def handle(self, record):
        """
        Calls :meth:`logging.Logger.handle` with unmodified arguments.
        """
        self._logger.handle(record)

    def addHandler(self, hdlr):
        """
        Calls :meth:`logging.Logger.addHandler` with unmodified arguments.
        """
        self._logger.addHandler(hdlr)

    def removeHandler(self, hdlr):
        """
        Calls :meth:`logging.Logger.removeHandler` with unmodified arguments.
        """
        self._logger.removeHandler(hdlr)

    def hasHandlers(self):
        """
        Calls :meth:`logging.Logger.hasHandlers` with unmodified arguments.

        Exists only in Python 3.
        """
        return self._logger.hasHandlers()

    def callHandlers(self, record):
        """
        Calls :meth:`logging.Logger.callHandlers` with unmodified arguments.
        """
        self._logger.callHandlers(record)

    def getEffectiveLevel(self):
        """
        Calls :meth:`logging.Logger.getEffectiveLevel` with unmodified
        arguments.
        """
        return self._logger.getEffectiveLevel()

    def isEnabledFor(self, level):
        """
        Calls :meth:`logging.Logger.isEnabledFor` with unmodified arguments.
        """
        return self._logger.isEnabledFor(level)

    def getChild(self, suffix):
        """
        Calls :meth:`logging.Logger.getChild` with unmodified arguments.
        """
        return self._logger.getChild(suffix)


class LoggerFactory(object):
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
    :type ignore_frame_names: ``list`` of ``str``
    """

    def __init__(self, ignore_frame_names=None):
        self._ignore = ignore_frame_names
        logging.setLoggerClass(_FixedFindCallerLogger)

    def __call__(self, *args):
        """
        Deduce the caller's module name and create a stdlib logger.

        If an optional argument is passed, it will be used as the logger name
        instead of guesswork.  This optional argument would be passed from the
        :func:`structlog.get_logger` call.  For example
        ``structlog.get_logger("foo")`` would cause this method to be called
        with ``"foo"`` as its first positional argument.

        :rtype: logging.Logger

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


class PositionalArgumentsFormatter(object):
    """
    Apply stdlib-like string formatting to the `event` key.

    If the `positional_args` key in the event dict is set, it must
    contain a tuple that is used for formatting (using the `%s` string
    formatting operator) of the value from the `event` key. This works
    in the same way as the stdlib handles arguments to the various log
    methods: if the tuple contains only a single `dict` argument it is
    used for keyword placeholders in the `event` string, otherwise it
    will be used for positional placeholders.

    `positional_args` is populated by :class:`structlog.stdlib.BoundLogger` or
    can be set manually.

    The `remove_positional_args` flag can be set to `False` to keep the
    `positional_args` key in the event dict; by default it will be
    removed from the event dict after formatting a message.
    """

    def __init__(self, remove_positional_args=True):
        self.remove_positional_args = remove_positional_args

    def __call__(self, _, __, event_dict):
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


# Adapted from the stdlib
CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

_NAME_TO_LEVEL = {
    "critical": CRITICAL,
    "exception": ERROR,
    "error": ERROR,
    "warn": WARNING,
    "warning": WARNING,
    "info": INFO,
    "debug": DEBUG,
    "notset": NOTSET,
}

_LEVEL_TO_NAME = dict(
    (v, k)
    for k, v in _NAME_TO_LEVEL.items()
    if k not in ("warn", "exception", "notset")
)


def filter_by_level(logger, name, event_dict):
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
    if logger.isEnabledFor(_NAME_TO_LEVEL[name]):
        return event_dict
    else:
        raise DropEvent


def add_log_level(logger, method_name, event_dict):
    """
    Add the log level to the event dict.
    """
    if method_name == "warn":
        # The stdlib has an alias
        method_name = "warning"

    event_dict["level"] = method_name
    return event_dict


def add_log_level_number(logger, method_name, event_dict):
    """
    Add the log level number to the event dict.

    Log level numbers map to the log level names. The Python stdlib uses them
    for filtering logic. This adds the same numbers so users can leverage
    similar filtering. Compare::

       level in ("warning", "error", "critical")
       level_number >= 30

    The mapping of names to numbers is in
    :data:`~structlog.stdlib._NAME_TO_LEVEL`.

    .. versionadded:: 18.2.0
    """
    event_dict["level_number"] = _NAME_TO_LEVEL[method_name]
    return event_dict


def add_logger_name(logger, method_name, event_dict):
    """
    Add the logger name to the event dict.
    """
    record = event_dict.get("_record")
    if record is None:
        event_dict["logger"] = logger.name
    else:
        event_dict["logger"] = record.name
    return event_dict


def render_to_log_kwargs(wrapped_logger, method_name, event_dict):
    """
    Render `event_dict` into keyword arguments for :func:`logging.log`.

    The `event` field is translated into `msg` and the rest of the `event_dict`
    is added as `extra`.

    This allows you to defer formatting to :mod:`logging`.

    .. versionadded:: 17.1.0
    """
    return {"msg": event_dict.pop("event"), "extra": event_dict}


class ProcessorFormatter(logging.Formatter):
    r"""
    Call ``structlog`` processors on :class:`logging.LogRecord`\ s.

    This :class:`logging.Formatter` allows to configure :mod:`logging` to call
    *processor* on ``structlog``-borne log entries (origin is determined solely
    on the fact whether the ``msg`` field on the :class:`logging.LogRecord` is
    a dict or not).

    This allows for two interesting use cases:

    #. You can format non-``structlog`` log entries.
    #. You can multiplex log records into multiple :class:`logging.Handler`\ s.

    Please refer to :doc:`standard-library` for examples.

    :param callable processor: A ``structlog`` processor.
    :param foreign_pre_chain:
        If not `None`, it is used as an iterable of processors that is applied
        to non-``structlog`` log entries before *processor*.  If `None`,
        formatting is left to :mod:`logging`. (default: `None`)
    :param bool keep_exc_info: ``exc_info`` on :class:`logging.LogRecord`\ s is
        added to the ``event_dict`` and removed afterwards. Set this to
        ``True`` to keep it on the :class:`logging.LogRecord`. (default: False)
    :param bool keep_stack_info: Same as *keep_exc_info* except for Python 3's
        ``stack_info``. (default: False)
    :param logger: Logger which we want to push through the ``structlog``
        processor chain. This parameter is necessary for some of the
        processors like `filter_by_level`. (default: None)
    :param bool pass_foreign_args: If True, pass a foreign log record's
        ``args`` attribute to the ``event_dict`` under ``positional_args`` key.
        (default: False)
    :rtype: str

    .. versionadded:: 17.1.0
    .. versionadded:: 17.2.0 *keep_exc_info* and *keep_stack_info*
    .. versionadded:: 19.2.0 *logger*
    .. versionadded:: 19.2.0 *pass_foreign_args*
    """

    def __init__(
        self,
        processor,
        foreign_pre_chain=None,
        keep_exc_info=False,
        keep_stack_info=False,
        logger=None,
        pass_foreign_args=False,
        *args,
        **kwargs
    ):
        fmt = kwargs.pop("fmt", "%(message)s")
        super(ProcessorFormatter, self).__init__(*args, fmt=fmt, **kwargs)
        self.processor = processor
        self.foreign_pre_chain = foreign_pre_chain
        self.keep_exc_info = keep_exc_info
        # The and clause saves us checking for PY3 in the formatter.
        self.keep_stack_info = keep_stack_info and PY3
        self.logger = logger
        self.pass_foreign_args = pass_foreign_args

    def format(self, record):
        """
        Extract ``structlog``'s `event_dict` from ``record.msg`` and format it.
        """
        # Make a shallow copy of the record to let other handlers/formatters
        # process the original one
        record = logging.makeLogRecord(record.__dict__)
        try:
            # Both attached by wrap_for_formatter
            logger = self.logger if self.logger is not None else record._logger
            meth_name = record._name

            # We need to copy because it's possible that the same record gets
            # processed by multiple logging formatters.  LogRecord.getMessage
            # would transform our dict into a str.
            ed = record.msg.copy()
        except AttributeError:
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
            if PY3 and record.stack_info:
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

        record.msg = self.processor(logger, meth_name, ed)
        return super(ProcessorFormatter, self).format(record)

    @staticmethod
    def wrap_for_formatter(logger, name, event_dict):
        """
        Wrap *logger*, *name*, and *event_dict*.

        The result is later unpacked by :class:`ProcessorFormatter` when
        formatting log entries.

        Use this static method as the renderer (i.e. final processor) if you
        want to use :class:`ProcessorFormatter` in your :mod:`logging`
        configuration.
        """
        return (event_dict,), {"extra": {"_logger": logger, "_name": name}}
