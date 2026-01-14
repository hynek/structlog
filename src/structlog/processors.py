# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Processors useful regardless of the logging framework.
"""

from __future__ import annotations

import datetime
import enum
import json
import logging
import operator
import os
import sys
import threading
import time

from collections.abc import (
    Collection,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from types import FrameType, TracebackType
from typing import (
    Any,
    Callable,
    ClassVar,
    NamedTuple,
    TextIO,
    cast,
)

from ._frames import (
    _find_first_app_frame_and_name,
    _format_exception,
    _format_stack,
)
from ._log_levels import NAME_TO_LEVEL, add_log_level
from ._utils import get_processname
from .tracebacks import ExceptionDictTransformer
from .typing import (
    EventDict,
    ExceptionTransformer,
    ExcInfo,
    WrappedLogger,
)


__all__ = [
    "NAME_TO_LEVEL",  # some people rely on it being here
    "CallsiteParameter",
    "CallsiteParameterAdder",
    "EventRenamer",
    "ExceptionPrettyPrinter",
    "JSONRenderer",
    "KeyValueRenderer",
    "LogfmtRenderer",
    "SensitiveDataRedactor",
    "StackInfoRenderer",
    "TimeStamper",
    "UnicodeDecoder",
    "UnicodeEncoder",
    "add_log_level",
    "dict_tracebacks",
    "format_exc_info",
]


class KeyValueRenderer:
    """
    Render ``event_dict`` as a list of ``Key=repr(Value)`` pairs.

    Args:
        sort_keys: Whether to sort keys when formatting.

        key_order:
            List of keys that should be rendered in this exact order.  Missing
            keys will be rendered as ``None``, extra keys depending on
            *sort_keys* and the dict class.

        drop_missing:
            When ``True``, extra keys in *key_order* will be dropped rather
            than rendered as ``None``.

        repr_native_str:
            When ``True``, :func:`repr()` is also applied to native strings.

    .. versionadded:: 0.2.0 *key_order*
    .. versionadded:: 16.1.0 *drop_missing*
    .. versionadded:: 17.1.0 *repr_native_str*
    """

    def __init__(
        self,
        sort_keys: bool = False,
        key_order: Sequence[str] | None = None,
        drop_missing: bool = False,
        repr_native_str: bool = True,
    ):
        self._ordered_items = _items_sorter(sort_keys, key_order, drop_missing)

        if repr_native_str is True:
            self._repr = repr
        else:

            def _repr(inst: Any) -> str:
                if isinstance(inst, str):
                    return inst

                return repr(inst)

            self._repr = _repr

    def __call__(
        self, _: WrappedLogger, __: str, event_dict: EventDict
    ) -> str:
        return " ".join(
            k + "=" + self._repr(v) for k, v in self._ordered_items(event_dict)
        )


class LogfmtRenderer:
    """
    Render ``event_dict`` using the logfmt_ format.

    .. _logfmt: https://brandur.org/logfmt

    Args:
        sort_keys: Whether to sort keys when formatting.

        key_order:
            List of keys that should be rendered in this exact order. Missing
            keys are rendered with empty values, extra keys depending on
            *sort_keys* and the dict class.

        drop_missing:
            When ``True``, extra keys in *key_order* will be dropped rather
            than rendered with empty values.

        bool_as_flag:
            When ``True``, render ``{"flag": True}`` as ``flag``, instead of
            ``flag=true``. ``{"flag": False}`` is always rendered as
            ``flag=false``.

    Raises:
        ValueError: If a key contains non-printable or whitespace characters.

    .. versionadded:: 21.5.0
    """

    def __init__(
        self,
        sort_keys: bool = False,
        key_order: Sequence[str] | None = None,
        drop_missing: bool = False,
        bool_as_flag: bool = True,
    ):
        self._ordered_items = _items_sorter(sort_keys, key_order, drop_missing)
        self.bool_as_flag = bool_as_flag

    def __call__(
        self, _: WrappedLogger, __: str, event_dict: EventDict
    ) -> str:
        elements: list[str] = []
        for key, value in self._ordered_items(event_dict):
            if any(c <= " " for c in key):
                msg = f'Invalid key: "{key}"'
                raise ValueError(msg)

            if value is None:
                elements.append(f"{key}=")
                continue

            if isinstance(value, bool):
                if self.bool_as_flag and value:
                    elements.append(f"{key}")
                    continue
                value = "true" if value else "false"

            value = str(value)
            backslashes_need_escaping = (
                " " in value or "=" in value or '"' in value
            )
            if backslashes_need_escaping and "\\" in value:
                value = value.replace("\\", "\\\\")

            value = value.replace('"', '\\"').replace("\n", "\\n")

            if backslashes_need_escaping:
                value = f'"{value}"'

            elements.append(f"{key}={value}")

        return " ".join(elements)


def _items_sorter(
    sort_keys: bool,
    key_order: Sequence[str] | None,
    drop_missing: bool,
) -> Callable[[EventDict], list[tuple[str, object]]]:
    """
    Return a function to sort items from an ``event_dict``.

    See `KeyValueRenderer` for an explanation of the parameters.
    """
    # Use an optimized version for each case.
    if key_order and sort_keys:

        def ordered_items(event_dict: EventDict) -> list[tuple[str, Any]]:
            items = []
            for key in key_order:
                value = event_dict.pop(key, None)
                if value is not None or not drop_missing:
                    items.append((key, value))

            items += sorted(event_dict.items())

            return items

    elif key_order:

        def ordered_items(event_dict: EventDict) -> list[tuple[str, Any]]:
            items = []
            for key in key_order:
                value = event_dict.pop(key, None)
                if value is not None or not drop_missing:
                    items.append((key, value))

            items += event_dict.items()

            return items

    elif sort_keys:

        def ordered_items(event_dict: EventDict) -> list[tuple[str, Any]]:
            return sorted(event_dict.items())

    else:
        ordered_items = operator.methodcaller(  # type: ignore[assignment]
            "items"
        )

    return ordered_items


class UnicodeEncoder:
    """
    Encode unicode values in ``event_dict``.

    Args:
        encoding: Encoding to encode to (default: ``"utf-8"``).

        errors:
            How to cope with encoding errors (default ``"backslashreplace"``).

    Just put it in the processor chain before the renderer.

    .. note:: Not very useful in a Python 3-only world.
    """

    _encoding: str
    _errors: str

    def __init__(
        self, encoding: str = "utf-8", errors: str = "backslashreplace"
    ) -> None:
        self._encoding = encoding
        self._errors = errors

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> EventDict:
        for key, value in event_dict.items():
            if isinstance(value, str):
                event_dict[key] = value.encode(self._encoding, self._errors)

        return event_dict


class UnicodeDecoder:
    """
    Decode byte string values in ``event_dict``.

    Args:
        encoding: Encoding to decode from (default: ``"utf-8"``).

        errors: How to cope with encoding errors (default: ``"replace"``).

    Useful to prevent ``b"abc"`` being rendered as as ``'b"abc"'``.

    Just put it in the processor chain before the renderer.

    .. versionadded:: 15.4.0
    """

    _encoding: str
    _errors: str

    def __init__(
        self, encoding: str = "utf-8", errors: str = "replace"
    ) -> None:
        self._encoding = encoding
        self._errors = errors

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> EventDict:
        for key, value in event_dict.items():
            if isinstance(value, bytes):
                event_dict[key] = value.decode(self._encoding, self._errors)

        return event_dict


class JSONRenderer:
    """
    Render the ``event_dict`` using ``serializer(event_dict, **dumps_kw)``.

    Args:
        dumps_kw:
            Are passed unmodified to *serializer*.  If *default* is passed, it
            will disable support for ``__structlog__``-based serialization.

        serializer:
            A :func:`json.dumps`-compatible callable that will be used to
            format the string.  This can be used to use alternative JSON
            encoders (default: :func:`json.dumps`).

            .. seealso:: :doc:`performance` for examples.

    .. versionadded:: 0.2.0 Support for ``__structlog__`` serialization method.
    .. versionadded:: 15.4.0 *serializer* parameter.
    .. versionadded:: 18.2.0
       Serializer's *default* parameter can be overwritten now.
    """

    def __init__(
        self,
        serializer: Callable[..., str | bytes] = json.dumps,
        **dumps_kw: Any,
    ) -> None:
        dumps_kw.setdefault("default", _json_fallback_handler)
        self._dumps_kw = dumps_kw
        self._dumps = serializer

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> str | bytes:
        """
        The return type of this depends on the return type of self._dumps.
        """
        return self._dumps(event_dict, **self._dumps_kw)


def _json_fallback_handler(obj: Any) -> Any:
    """
    Serialize custom datatypes and pass the rest to __structlog__ & repr().
    """
    # circular imports :(
    from structlog.threadlocal import _ThreadLocalDictWrapper

    if isinstance(obj, _ThreadLocalDictWrapper):
        return obj._dict

    try:
        return obj.__structlog__()
    except AttributeError:
        return repr(obj)


class ExceptionRenderer:
    """
    Replace an ``exc_info`` field with an ``exception`` field which is rendered
    by *exception_formatter*.

    The contents of the ``exception`` field depends on the return value of the
    *exception_formatter* that is passed:

    - The default produces a formatted string via Python's built-in traceback
      formatting (this is :obj:`.format_exc_info`).
    - If you pass a :class:`~structlog.tracebacks.ExceptionDictTransformer`, it
      becomes a list of stack dicts that can be serialized to JSON.

    If *event_dict* contains the key ``exc_info``, there are three possible
    behaviors:

    1. If the value is a tuple, render it into the key ``exception``.
    2. If the value is an Exception render it into the key ``exception``.
    3. If the value true but no tuple, obtain exc_info ourselves and render
       that.

    If there is no ``exc_info`` key, the *event_dict* is not touched. This
    behavior is analog to the one of the stdlib's logging.

    Args:
        exception_formatter:
            A callable that is used to format the exception from the
            ``exc_info`` field into the ``exception`` field.

    .. seealso::
        :doc:`exceptions` for a broader explanation of *structlog*'s exception
        features.

    .. versionadded:: 22.1.0
    """

    def __init__(
        self,
        exception_formatter: ExceptionTransformer = _format_exception,
    ) -> None:
        self.format_exception = exception_formatter

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> EventDict:
        exc_info = _figure_out_exc_info(event_dict.pop("exc_info", None))
        if exc_info:
            event_dict["exception"] = self.format_exception(exc_info)

        return event_dict


format_exc_info = ExceptionRenderer()
"""
Replace an ``exc_info`` field with an ``exception`` string field using Python's
built-in traceback formatting.

If *event_dict* contains the key ``exc_info``, there are three possible
behaviors:

1. If the value is a tuple, render it into the key ``exception``.
2. If the value is an Exception render it into the key ``exception``.
3. If the value is true but no tuple, obtain exc_info ourselves and render
   that.

If there is no ``exc_info`` key, the *event_dict* is not touched. This behavior
is analog to the one of the stdlib's logging.

.. seealso::
    :doc:`exceptions` for a broader explanation of *structlog*'s exception
    features.
"""

dict_tracebacks = ExceptionRenderer(ExceptionDictTransformer())
"""
Replace an ``exc_info`` field with an ``exception`` field containing structured
tracebacks suitable for, e.g., JSON output.

It is a shortcut for :class:`ExceptionRenderer` with a
:class:`~structlog.tracebacks.ExceptionDictTransformer`.

The treatment of the ``exc_info`` key is identical to `format_exc_info`.

.. versionadded:: 22.1.0

.. seealso::
    :doc:`exceptions` for a broader explanation of *structlog*'s exception
    features.
"""


class TimeStamper:
    """
    Add a timestamp to ``event_dict``.

    Args:
        fmt:
            strftime format string, or ``"iso"`` for `ISO 8601
            <https://en.wikipedia.org/wiki/ISO_8601>`_, or `None` for a `UNIX
            timestamp <https://en.wikipedia.org/wiki/Unix_time>`_.

        utc: Whether timestamp should be in UTC or local time.

        key: Target key in *event_dict* for added timestamps.

    .. versionchanged:: 19.2.0 Can be pickled now.
    """

    __slots__ = ("_stamper", "fmt", "key", "utc")

    def __init__(
        self,
        fmt: str | None = None,
        utc: bool = True,
        key: str = "timestamp",
    ) -> None:
        self.fmt, self.utc, self.key = fmt, utc, key

        self._stamper = _make_stamper(fmt, utc, key)

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> EventDict:
        return self._stamper(event_dict)

    def __getstate__(self) -> dict[str, Any]:
        return {"fmt": self.fmt, "utc": self.utc, "key": self.key}

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.fmt = state["fmt"]
        self.utc = state["utc"]
        self.key = state["key"]

        self._stamper = _make_stamper(**state)


def _make_stamper(
    fmt: str | None, utc: bool, key: str
) -> Callable[[EventDict], EventDict]:
    """
    Create a stamper function.
    """
    if fmt is None and not utc:
        msg = "UNIX timestamps are always UTC."
        raise ValueError(msg)

    now: Callable[[], datetime.datetime]

    if utc:

        def now() -> datetime.datetime:
            return datetime.datetime.now(tz=datetime.timezone.utc)

    else:

        def now() -> datetime.datetime:
            # We don't need the TZ for our own formatting. We add it only for
            # user-defined formats later.
            return datetime.datetime.now()  # noqa: DTZ005

    if fmt is None:

        def stamper_unix(event_dict: EventDict) -> EventDict:
            event_dict[key] = time.time()

            return event_dict

        return stamper_unix

    if fmt.upper() == "ISO":

        def stamper_iso_local(event_dict: EventDict) -> EventDict:
            event_dict[key] = now().isoformat()
            return event_dict

        def stamper_iso_utc(event_dict: EventDict) -> EventDict:
            event_dict[key] = now().isoformat().replace("+00:00", "Z")
            return event_dict

        if utc:
            return stamper_iso_utc

        return stamper_iso_local

    def stamper_fmt_local(event_dict: EventDict) -> EventDict:
        event_dict[key] = now().astimezone().strftime(fmt)
        return event_dict

    def stamper_fmt_utc(event_dict: EventDict) -> EventDict:
        event_dict[key] = now().strftime(fmt)
        return event_dict

    if utc:
        return stamper_fmt_utc

    return stamper_fmt_local


class MaybeTimeStamper:
    """
    A timestamper that only adds a timestamp if there is none.

    This allows you to overwrite the ``timestamp`` key in the event dict for
    example when the event is coming from another system.

    It takes the same arguments as `TimeStamper`.

    .. versionadded:: 23.2.0
    """

    __slots__ = ("stamper",)

    def __init__(
        self,
        fmt: str | None = None,
        utc: bool = True,
        key: str = "timestamp",
    ):
        self.stamper = TimeStamper(fmt=fmt, utc=utc, key=key)

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> EventDict:
        if self.stamper.key not in event_dict:
            return self.stamper(logger, name, event_dict)

        return event_dict


def _figure_out_exc_info(v: Any) -> ExcInfo | None:
    """
    Try to convert *v* into an ``exc_info`` tuple.

    Return ``None`` if *v* does not represent an exception or if there is no
    current exception.
    """
    if isinstance(v, BaseException):
        return (v.__class__, v, v.__traceback__)

    if isinstance(v, tuple) and len(v) == 3:
        has_type = isinstance(v[0], type) and issubclass(v[0], BaseException)
        has_exc = isinstance(v[1], BaseException)
        has_tb = v[2] is None or isinstance(v[2], TracebackType)
        if has_type and has_exc and has_tb:
            return v

    if v:
        result = sys.exc_info()
        if result == (None, None, None):
            return None
        return cast(ExcInfo, result)

    return None


class ExceptionPrettyPrinter:
    """
    Pretty print exceptions rendered by *exception_formatter* and remove them
    from the ``event_dict``.

    Args:
        file: Target file for output (default: ``sys.stdout``).
        exception_formatter:
            A callable that is used to format the exception from the
            ``exc_info`` field into the ``exception`` field.

    This processor is mostly for development and testing so you can read
    exceptions properly formatted.

    It behaves like `format_exc_info`, except that it removes the exception data
    from the event dictionary after printing it using the passed
    *exception_formatter*, which defaults to Python's built-in traceback formatting.

    It's tolerant to having `format_exc_info` in front of itself in the
    processor chain but doesn't require it.  In other words, it handles both
    ``exception`` as well as ``exc_info`` keys.

    .. versionadded:: 0.4.0

    .. versionchanged:: 16.0.0
       Added support for passing exceptions as ``exc_info`` on Python 3.

    .. versionchanged:: 25.4.0
       Fixed *exception_formatter* so that it overrides the default if set.
    """

    def __init__(
        self,
        file: TextIO | None = None,
        exception_formatter: ExceptionTransformer = _format_exception,
    ) -> None:
        self.format_exception = exception_formatter
        if file is not None:
            self._file = file
        else:
            self._file = sys.stdout

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> EventDict:
        exc = event_dict.pop("exception", None)
        if exc is None:
            exc_info = _figure_out_exc_info(event_dict.pop("exc_info", None))
            if exc_info:
                exc = self.format_exception(exc_info)

        if exc:
            print(exc, file=self._file)

        return event_dict


class StackInfoRenderer:
    """
    Add stack information with key ``stack`` if ``stack_info`` is `True`.

    Useful when you want to attach a stack dump to a log entry without
    involving an exception and works analogously to the *stack_info* argument
    of the Python standard library logging.

    Args:
        additional_ignores:
            By default, stack frames coming from *structlog* are ignored. With
            this argument you can add additional names that are ignored, before
            the stack starts being rendered. They are matched using
            ``startswith()``, so they don't have to match exactly. The names
            are used to find the first relevant name, therefore once a frame is
            found that doesn't start with *structlog* or one of
            *additional_ignores*, **no filtering** is applied to subsequent
            frames.

    .. versionadded:: 0.4.0
    .. versionadded:: 22.1.0  *additional_ignores*
    """

    __slots__ = ("_additional_ignores",)

    def __init__(self, additional_ignores: list[str] | None = None) -> None:
        self._additional_ignores = additional_ignores

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> EventDict:
        if event_dict.pop("stack_info", None):
            event_dict["stack"] = _format_stack(
                _find_first_app_frame_and_name(self._additional_ignores)[0]
            )

        return event_dict


class CallsiteParameter(enum.Enum):
    """
    Callsite parameters that can be added to an event dictionary with the
    `structlog.processors.CallsiteParameterAdder` processor class.

    The string values of the members of this enum will be used as the keys for
    the callsite parameters in the event dictionary.

    .. versionadded:: 21.5.0

    .. versionadded:: 25.5.0
       `QUAL_NAME` parameter.
    """

    #: The full path to the python source file of the callsite.
    PATHNAME = "pathname"
    #: The basename part of the full path to the python source file of the
    #: callsite.
    FILENAME = "filename"
    #: The python module the callsite was in. This mimics the module attribute
    #: of `logging.LogRecord` objects and will be the basename, without
    #: extension, of the full path to the python source file of the callsite.
    MODULE = "module"
    #: The name of the function that the callsite was in.
    FUNC_NAME = "func_name"
    #: The qualified name of the callsite (includes scope and class names).
    #: Requires Python 3.11+.
    QUAL_NAME = "qual_name"
    #: The line number of the callsite.
    LINENO = "lineno"
    #: The ID of the thread the callsite was executed in.
    THREAD = "thread"
    #: The name of the thread the callsite was executed in.
    THREAD_NAME = "thread_name"
    #: The ID of the process the callsite was executed in.
    PROCESS = "process"
    #: The name of the process the callsite was executed in.
    PROCESS_NAME = "process_name"


def _get_callsite_pathname(module: str, frame: FrameType) -> Any:
    return frame.f_code.co_filename


def _get_callsite_filename(module: str, frame: FrameType) -> Any:
    return os.path.basename(frame.f_code.co_filename)


def _get_callsite_module(module: str, frame: FrameType) -> Any:
    return os.path.splitext(os.path.basename(frame.f_code.co_filename))[0]


def _get_callsite_func_name(module: str, frame: FrameType) -> Any:
    return frame.f_code.co_name


def _get_callsite_qual_name(module: str, frame: FrameType) -> Any:
    return frame.f_code.co_qualname  # will crash on Python <3.11


def _get_callsite_lineno(module: str, frame: FrameType) -> Any:
    return frame.f_lineno


def _get_callsite_thread(module: str, frame: FrameType) -> Any:
    return threading.get_ident()


def _get_callsite_thread_name(module: str, frame: FrameType) -> Any:
    return threading.current_thread().name


def _get_callsite_process(module: str, frame: FrameType) -> Any:
    return os.getpid()


def _get_callsite_process_name(module: str, frame: FrameType) -> Any:
    return get_processname()


class CallsiteParameterAdder:
    """
    Adds parameters of the callsite that an event dictionary originated from to
    the event dictionary. This processor can be used to enrich events
    dictionaries with information such as the function name, line number and
    filename that an event dictionary originated from.

    If the event dictionary has an embedded `logging.LogRecord` object and did
    not originate from *structlog* then the callsite information will be
    determined from the `logging.LogRecord` object. For event dictionaries
    without an embedded `logging.LogRecord` object the callsite will be
    determined from the stack trace, ignoring all intra-structlog calls, calls
    from the `logging` module, and stack frames from modules with names that
    start with values in ``additional_ignores``, if it is specified.

    The keys used for callsite parameters in the event dictionary are the
    string values of `CallsiteParameter` enum members.

    Args:
        parameters:
            A collection of `CallsiteParameter` values that should be added to
            the event dictionary.

        additional_ignores:
            Additional names with which a stack frame's module name must not
            start for it to be considered when determening the callsite.

    .. note::

        When used with `structlog.stdlib.ProcessorFormatter` the most efficient
        configuration is to either use this processor in ``foreign_pre_chain``
        of `structlog.stdlib.ProcessorFormatter` and in ``processors`` of
        `structlog.configure`, or to use it in ``processors`` of
        `structlog.stdlib.ProcessorFormatter` without using it in
        ``processors`` of `structlog.configure` and ``foreign_pre_chain`` of
        `structlog.stdlib.ProcessorFormatter`.

    .. versionadded:: 21.5.0
    """

    _handlers: ClassVar[
        dict[CallsiteParameter, Callable[[str, FrameType], Any]]
    ] = {
        # We can't use lambda functions here because they are not pickleable.
        CallsiteParameter.PATHNAME: _get_callsite_pathname,
        CallsiteParameter.FILENAME: _get_callsite_filename,
        CallsiteParameter.MODULE: _get_callsite_module,
        CallsiteParameter.FUNC_NAME: _get_callsite_func_name,
        CallsiteParameter.QUAL_NAME: _get_callsite_qual_name,
        CallsiteParameter.LINENO: _get_callsite_lineno,
        CallsiteParameter.THREAD: _get_callsite_thread,
        CallsiteParameter.THREAD_NAME: _get_callsite_thread_name,
        CallsiteParameter.PROCESS: _get_callsite_process,
        CallsiteParameter.PROCESS_NAME: _get_callsite_process_name,
    }
    _record_attribute_map: ClassVar[dict[CallsiteParameter, str]] = {
        CallsiteParameter.PATHNAME: "pathname",
        CallsiteParameter.FILENAME: "filename",
        CallsiteParameter.MODULE: "module",
        CallsiteParameter.FUNC_NAME: "funcName",
        CallsiteParameter.LINENO: "lineno",
        CallsiteParameter.THREAD: "thread",
        CallsiteParameter.THREAD_NAME: "threadName",
        CallsiteParameter.PROCESS: "process",
        CallsiteParameter.PROCESS_NAME: "processName",
    }

    _all_parameters: ClassVar[set[CallsiteParameter]] = set(CallsiteParameter)

    class _RecordMapping(NamedTuple):
        event_dict_key: str
        record_attribute: str

    __slots__ = ("_active_handlers", "_additional_ignores", "_record_mappings")

    def __init__(
        self,
        parameters: Collection[CallsiteParameter] = _all_parameters,
        additional_ignores: list[str] | None = None,
    ) -> None:
        if additional_ignores is None:
            additional_ignores = []
        # Ignore stack frames from the logging module. They will occur if this
        # processor is used in ProcessorFormatter, and additionally the logging
        # module should not be logging using structlog.
        self._additional_ignores = ["logging", *additional_ignores]
        self._active_handlers: list[
            tuple[CallsiteParameter, Callable[[str, FrameType], Any]]
        ] = []
        self._record_mappings: list[CallsiteParameterAdder._RecordMapping] = []
        for parameter in parameters:
            self._active_handlers.append(
                (parameter, self._handlers[parameter])
            )
            if (
                record_attr := self._record_attribute_map.get(parameter)
            ) is not None:
                self._record_mappings.append(
                    self._RecordMapping(
                        parameter.value,
                        record_attr,
                    )
                )

    def __call__(
        self, logger: logging.Logger, name: str, event_dict: EventDict
    ) -> EventDict:
        record: logging.LogRecord | None = event_dict.get("_record")
        from_structlog: bool = event_dict.get("_from_structlog", False)

        # If the event dictionary has a record, but it comes from structlog,
        # then the callsite parameters of the record will not be correct.
        if record is not None and not from_structlog:
            for mapping in self._record_mappings:
                event_dict[mapping.event_dict_key] = record.__dict__[
                    mapping.record_attribute
                ]

            return event_dict

        frame, module = _find_first_app_frame_and_name(
            additional_ignores=self._additional_ignores
        )
        for parameter, handler in self._active_handlers:
            event_dict[parameter.value] = handler(module, frame)

        return event_dict


class EventRenamer:
    r"""
    Rename the ``event`` key in event dicts.

    This is useful if you want to use consistent log message keys across
    platforms and/or use the ``event`` key for something custom.

    .. warning::

       It's recommended to put this processor right before the renderer, since
       some processors may rely on the presence and meaning of the ``event``
       key.

    Args:
        to: Rename ``event_dict["event"]`` to ``event_dict[to]``

        replace_by:
            Rename ``event_dict[replace_by]`` to ``event_dict["event"]``.
            *replace_by* missing from ``event_dict`` is handled gracefully.

    .. versionadded:: 22.1.0

    See also the :ref:`rename-event` recipe.
    """

    def __init__(self, to: str, replace_by: str | None = None):
        self.to = to
        self.replace_by = replace_by

    def __call__(
        self, logger: logging.Logger, name: str, event_dict: EventDict
    ) -> EventDict:
        event = event_dict.pop("event")
        event_dict[self.to] = event

        if self.replace_by is not None:
            replace_by = event_dict.pop(self.replace_by, None)
            if replace_by is not None:
                event_dict["event"] = replace_by

        return event_dict


def _compile_sensitive_pattern(
    pattern: str, case_insensitive: bool
) -> Callable[[str], bool]:
    """
    Compile a glob-style pattern into a matcher function.

    Args:
        pattern: A glob-style pattern string containing ``*`` and/or ``?``.
        case_insensitive: Whether matching should ignore case.

    Returns:
        A function that takes a string key and returns True if it matches
        the pattern.

    Note:
        Uses :func:`fnmatch.translate` to convert glob patterns to regex.
        ``*`` matches any sequence of characters (including empty).
        ``?`` matches exactly one character.
    """
    import fnmatch
    import re

    # Convert glob pattern to regex
    regex_pattern = fnmatch.translate(pattern)
    flags = re.IGNORECASE if case_insensitive else 0
    compiled = re.compile(regex_pattern, flags)

    def matcher(key: str) -> bool:
        return compiled.fullmatch(key) is not None

    return matcher


#: Type alias for the redaction callback function.
#:



class SensitiveDataRedactor:
    """
    Redact sensitive fields from event dictionaries.

    This processor automatically identifies and redacts sensitive data from log
    events before they are written to log destinations. It is designed to help
    with data protection compliance (GDPR, HIPAA, PCI-DSS, etc.) by ensuring
    that sensitive information like passwords, API keys, personal data, and
    other confidential fields are not exposed in logs.

    The processor supports:

    - **Exact field matching**: Specify exact field names to redact.
    - **Pattern matching**: Use glob-style patterns (``*`` and ``?``) to match
      field names dynamically.
    - **Case-insensitive matching**: Optionally ignore case when matching field
      names.
    - **Nested structures**: Automatically traverses nested dictionaries and
      lists to find and redact sensitive fields at any depth.
    - **Custom redaction**: Provide a callback function for custom redaction
      logic (e.g., partial masking, hashing).
    - **Audit logging**: Track redaction events for compliance auditing.

    Args:
        sensitive_fields:
            A collection of field names or glob-style patterns to redact.

            **Exact matches**: Simple strings match field names exactly::

                ["password", "api_key", "ssn"]

            **Glob patterns**: Use ``*`` to match any sequence of characters,
            and ``?`` to match exactly one character::

                ["*password*"]     # Matches: password, user_password, password_hash
                ["api_*"]          # Matches: api_key, api_secret, api_token
                ["*_token"]        # Matches: auth_token, refresh_token
                ["key?"]           # Matches: key1, key2, keyA (but not key or key12)

            Common sensitive field patterns for compliance:

            - **Authentication**: ``*password*``, ``*secret*``, ``*token*``,
              ``*credential*``, ``*api_key*``
            - **Personal Data (GDPR)**: ``*email*``, ``*phone*``, ``*address*``,
              ``*ssn*``, ``*birth*``, ``*name*``
            - **Financial (PCI-DSS)**: ``*card*``, ``*cvv*``, ``*account*``,
              ``*routing*``
            - **Health (HIPAA)**: ``*diagnosis*``, ``*prescription*``,
              ``*medical*``, ``*health*``

        placeholder:
            The string used to replace redacted values. Default is
            ``"[REDACTED]"``. This parameter is ignored if *redaction_callback*
            is provided.

            Examples of common placeholders::

                "[REDACTED]"           # Default, clear indication of redaction
                "***"                  # Shorter placeholder
                "<SENSITIVE>"          # Alternative marker
                ""                     # Empty string (removes value)

        case_insensitive:
            When ``True``, field name matching ignores case. Default is
            ``False``.

            This is useful when field names may have inconsistent casing::

                # With case_insensitive=True, matches: password, PASSWORD, Password
                SensitiveDataRedactor(["password"], case_insensitive=True)

        redaction_callback:
            An optional callable for custom redaction logic. When provided,
            this takes precedence over *placeholder*.

            The callback receives three arguments:

            - ``field_name`` (str): The name of the field being redacted.
            - ``original_value`` (Any): The original value before redaction.
            - ``field_path`` (str): The full path to the field in dot notation
              (e.g., ``"config.database.password"`` or ``"users[0].ssn"``).

            The callback should return the redacted value.

            Example - Partial masking for debugging::

                def partial_mask(field_name, value, path):
                    if isinstance(value, str) and len(value) > 4:
                        return value[:2] + "*" * (len(value) - 4) + value[-2:]
                    return "[REDACTED]"

            Example - Hash sensitive values for correlation::

                import hashlib
                def hash_value(field_name, value, path):
                    h = hashlib.sha256(str(value).encode()).hexdigest()[:8]
                    return f"[HASH:{h}]"

        audit_callback:
            An optional callable invoked for each redacted field, useful for
            compliance auditing and monitoring.

            The callback receives the same three arguments as *redaction_callback*
            but returns nothing. It is called *before* the value is redacted,
            so it receives the original value.

            Example - Log redaction events::

                import logging
                audit_logger = logging.getLogger("security.audit")

                def audit_redaction(field_name, value, path):
                    audit_logger.info(
                        "Redacted sensitive field",
                        extra={"field": field_name, "path": path}
                    )

            Example - Count redactions for metrics::

                from collections import Counter
                redaction_counts = Counter()

                def count_redactions(field_name, value, path):
                    redaction_counts[field_name] += 1

    Attributes:
        This class uses ``__slots__`` for memory efficiency and does not expose
        public attributes. Use the constructor parameters to configure behavior.



    Examples:
        **Basic usage**::

            from structlog.processors import SensitiveDataRedactor

            redactor = SensitiveDataRedactor(
                sensitive_fields=["password", "api_key", "secret"]
            )

            # In structlog configuration
            structlog.configure(
                processors=[
                    structlog.stdlib.add_log_level,
                    redactor,  # Add before renderers
                    structlog.processors.JSONRenderer(),
                ]
            )

        **Nested dictionary handling**::

            redactor = SensitiveDataRedactor(sensitive_fields=["password"])
            event = {
                "user": "alice",
                "credentials": {
                    "password": "secret123",
                    "mfa_enabled": True
                }
            }
            result = redactor(None, None, event)
            # Result: {"user": "alice", "credentials": {"password": "[REDACTED]", "mfa_enabled": True}}

        **Pattern matching for flexible redaction**::

            redactor = SensitiveDataRedactor(
                sensitive_fields=[
                    "*password*",    # Any field containing "password"
                    "api_*",         # Any field starting with "api_"
                    "*_token",       # Any field ending with "_token"
                ]
            )

        **Case-insensitive matching**::

            redactor = SensitiveDataRedactor(
                sensitive_fields=["password", "apikey"],
                case_insensitive=True
            )
            # Matches: password, PASSWORD, Password, ApiKey, APIKEY, etc.

        **Custom redaction with partial masking**::

            def mask_email(field_name, value, path):
                if field_name == "email" and "@" in str(value):
                    local, domain = str(value).split("@")
                    return f"{local[0]}***@{domain}"
                return "[REDACTED]"

            redactor = SensitiveDataRedactor(
                sensitive_fields=["email", "password"],
                redaction_callback=mask_email
            )

        **GDPR compliance with audit trail**::

            import logging

            # Separate audit logger for compliance records
            audit_logger = logging.getLogger("gdpr.audit")

            def gdpr_audit(field_name, value, path):
                audit_logger.info(
                    "PII field redacted for GDPR compliance",
                    extra={
                        "field_name": field_name,
                        "field_path": path,
                        "value_type": type(value).__name__,
                    }
                )

            gdpr_redactor = SensitiveDataRedactor(
                sensitive_fields=[
                    "*email*", "*phone*", "*address*",
                    "*name*", "*birth*", "*ssn*", "*passport*",
                ],
                case_insensitive=True,
                audit_callback=gdpr_audit,
            )

        **PCI-DSS compliance for payment data**::

            def mask_card_number(field_name, value, path):
                if "card" in field_name.lower() and isinstance(value, str):
                    if len(value) >= 4:
                        return f"****-****-****-{value[-4:]}"
                return "[REDACTED]"

            pci_redactor = SensitiveDataRedactor(
                sensitive_fields=[
                    "*card*", "*cvv*", "*cvc*",
                    "*account_number*", "*routing*",
                ],
                case_insensitive=True,
                redaction_callback=mask_card_number,
            )

    Note:
        - Place this processor **before** any renderers (like ``JSONRenderer``)
          in your processor chain to ensure sensitive data is redacted before
          being serialized.
        - The processor modifies the event dictionary in place for efficiency.
        - For performance-critical applications with many sensitive fields,
          prefer exact matches over patterns where possible.
        - The processor is pickleable, allowing it to be used with multiprocessing.

    See Also:
        - :doc:`/processors` for general information about processors.
        - :class:`JSONRenderer` for rendering redacted logs as JSON.

    .. versionadded:: 25.1.0
    """

    __slots__ = (
        "_audit_callback",
        "_case_insensitive",
        "_exact_fields",
        "_pattern_matchers",
        "_placeholder",
        "_redaction_callback",
        "_sensitive_fields",
    )

    _exact_fields: frozenset[str]
    _pattern_matchers: tuple[Callable[[str], bool], ...]
    _placeholder: str
    _case_insensitive: bool
    _sensitive_fields: tuple[str, ...]
    _redaction_callback: Callable[[str, Any, str], Any] | None
    _audit_callback: Callable[[str, Any, str], None] | None

    def __init__(
        self,
        sensitive_fields: Collection[str],
        placeholder: str = "[REDACTED]",
        case_insensitive: bool = False,
        redaction_callback: Callable[[str, Any, str], Any] | None = None,
        audit_callback: Callable[[str, Any, str], None] | None = None,
    ) -> None:
        """
        Initialize the SensitiveDataRedactor processor.

        Args:
            sensitive_fields: Field names or patterns to redact.
            placeholder: Replacement string for redacted values.
            case_insensitive: Whether to ignore case when matching.
            redaction_callback: Custom function for redaction logic.
            audit_callback: Function called for each redaction event.
        """
        self._placeholder = placeholder
        self._case_insensitive = case_insensitive
        self._redaction_callback = redaction_callback
        self._audit_callback = audit_callback
        # Store original fields for pickling
        self._sensitive_fields = tuple(sensitive_fields)

        # Separate exact matches from patterns for optimized matching
        exact_fields: list[str] = []
        pattern_matchers: list[Callable[[str], bool]] = []

        for field in sensitive_fields:
            if "*" in field or "?" in field:
                # It's a glob pattern - compile to regex matcher
                pattern_matchers.append(
                    _compile_sensitive_pattern(field, case_insensitive)
                )
            # Exact match - normalize case if needed
            elif case_insensitive:
                exact_fields.append(field.lower())
            else:
                exact_fields.append(field)

        self._exact_fields = frozenset(exact_fields)
        self._pattern_matchers = tuple(pattern_matchers)

    def _is_sensitive(self, key: str) -> bool:
        """
        Check if a field key matches any sensitive field or pattern.

        Args:
            key: The field name to check.

        Returns:
            True if the key matches a sensitive field or pattern, False otherwise.

        Note:
            Exact matches are checked first (O(1) lookup) before falling back
            to pattern matching for better performance.
        """
        check_key = key.lower() if self._case_insensitive else key

        # Check exact matches first (fast path - O(1) frozenset lookup)
        if check_key in self._exact_fields:
            return True

        # Check patterns (slower path - iterate through compiled patterns)
        return any(matcher(key) for matcher in self._pattern_matchers)

    def _get_redacted_value(self, key: str, value: Any, path: str) -> Any:
        """
        Compute the redacted value for a sensitive field.

        This method first calls the audit callback (if configured), then
        determines the replacement value using either the custom redaction
        callback or the default placeholder.

        Args:
            key: The field name being redacted.
            value: The original value to redact.
            path: The full dot-separated path to the field.

        Returns:
            The redacted value to use as replacement.
        """
        # Call audit callback before redaction if provided
        if self._audit_callback is not None:
            self._audit_callback(key, value, path)

        # Use custom callback if provided, otherwise use placeholder
        if self._redaction_callback is not None:
            return self._redaction_callback(key, value, path)
        return self._placeholder

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> EventDict:
        """
        Process an event dictionary, redacting sensitive fields.

        This is the main entry point called by structlog's processor chain.

        Args:
            logger: The wrapped logger instance (unused by this processor).
            name: The name of the log method called (unused by this processor).
            event_dict: The event dictionary to process.

        Returns:
            The modified event dictionary with sensitive fields redacted.

        Note:
            The event dictionary is modified in place for efficiency.
        """
        return self._redact_dict(event_dict, "")

    def _redact_dict(
        self, d: MutableMapping[str, Any], parent_path: str
    ) -> MutableMapping[str, Any]:
        """
        Recursively redact sensitive fields from a dictionary.

        Args:
            d: The dictionary to process.
            parent_path: The dot-separated path to this dictionary's location.

        Returns:
            The same dictionary with sensitive fields redacted.
        """
        for key, value in d.items():
            current_path = f"{parent_path}.{key}" if parent_path else key
            if self._is_sensitive(key):
                d[key] = self._get_redacted_value(key, value, current_path)
            elif isinstance(value, dict):
                d[key] = self._redact_dict(value, current_path)
            elif isinstance(value, list):
                d[key] = self._redact_list(value, current_path)
        return d

    def _redact_list(
        self, lst: MutableSequence[Any], parent_path: str
    ) -> MutableSequence[Any]:
        """
        Recursively redact sensitive fields from items in a list.

        Args:
            lst: The list to process.
            parent_path: The dot-separated path to this list's location.

        Returns:
            The same list with sensitive fields in nested structures redacted.
        """
        for i, item in enumerate(lst):
            current_path = f"{parent_path}[{i}]"
            if isinstance(item, dict):
                lst[i] = self._redact_dict(item, current_path)
            elif isinstance(item, list):
                lst[i] = self._redact_list(item, current_path)
        return lst

    def __getstate__(self) -> dict[str, Any]:
        """
        Get state for pickling.

        Returns:
            A dictionary containing all configuration needed to reconstruct
            this processor instance.
        """
        return {
            "sensitive_fields": self._sensitive_fields,
            "placeholder": self._placeholder,
            "case_insensitive": self._case_insensitive,
            "redaction_callback": self._redaction_callback,
            "audit_callback": self._audit_callback,
        }

    def __setstate__(self, state: dict[str, Any]) -> None:
        """
        Restore state after unpickling.

        Args:
            state: The state dictionary from ``__getstate__``.
        """
        sensitive_fields = state["sensitive_fields"]
        case_insensitive = state["case_insensitive"]

        self._placeholder = state["placeholder"]
        self._case_insensitive = case_insensitive
        self._redaction_callback = state.get("redaction_callback")
        self._audit_callback = state.get("audit_callback")
        self._sensitive_fields = tuple(sensitive_fields)

        # Rebuild exact fields and pattern matchers
        exact_fields: list[str] = []
        pattern_matchers: list[Callable[[str], bool]] = []

        for field in sensitive_fields:
            if "*" in field or "?" in field:
                pattern_matchers.append(
                    _compile_sensitive_pattern(field, case_insensitive)
                )
            elif case_insensitive:
                exact_fields.append(field.lower())
            else:
                exact_fields.append(field)

        self._exact_fields = frozenset(exact_fields)
        self._pattern_matchers = tuple(pattern_matchers)
