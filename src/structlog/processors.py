# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Processors useful regardless of the logging framework.
"""
import datetime
import json
import operator
import sys
import time

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    TextIO,
    Tuple,
    Union,
)

from ._frames import (
    _find_first_app_frame_and_name,
    _format_exception,
    _format_stack,
)
from ._log_levels import _NAME_TO_LEVEL, add_log_level
from .types import EventDict, ExcInfo, WrappedLogger


__all__ = [
    "_NAME_TO_LEVEL",  # some people rely on it being here
    "KeyValueRenderer",
    "TimeStamper",
    "add_log_level",
    "UnicodeEncoder",
    "UnicodeDecoder",
    "JSONRenderer",
    "format_exc_info",
    "ExceptionPrettyPrinter",
    "StackInfoRenderer",
]


class KeyValueRenderer:
    """
    Render ``event_dict`` as a list of ``Key=repr(Value)`` pairs.

    :param sort_keys: Whether to sort keys when formatting.
    :param key_order: List of keys that should be rendered in this exact
        order.  Missing keys will be rendered as ``None``, extra keys depending
        on *sort_keys* and the dict class.
    :param drop_missing: When ``True``, extra keys in *key_order* will be
        dropped rather than rendered as ``None``.
    :param repr_native_str: When ``True``, :func:`repr()` is also applied
        to native strings (i.e. unicode on Python 3 and bytes on Python 2).
        Setting this to ``False`` is useful if you want to have human-readable
        non-ASCII output on Python 2.

    .. versionadded:: 0.2.0 *key_order*
    .. versionadded:: 16.1.0 *drop_missing*
    .. versionadded:: 17.1.0 *repr_native_str*
    """

    def __init__(
        self,
        sort_keys: bool = False,
        key_order: Optional[Sequence[str]] = None,
        drop_missing: bool = False,
        repr_native_str: bool = True,
    ):
        # Use an optimized version for each case.
        if key_order and sort_keys is True:

            def ordered_items(event_dict: EventDict) -> List[Tuple[str, Any]]:
                items = []
                for key in key_order:  # type: ignore
                    value = event_dict.pop(key, None)
                    if value is not None or not drop_missing:
                        items.append((key, value))

                items += sorted(event_dict.items())

                return items

        elif key_order:

            def ordered_items(event_dict: EventDict) -> List[Tuple[str, Any]]:
                items = []
                for key in key_order:  # type: ignore
                    value = event_dict.pop(key, None)
                    if value is not None or not drop_missing:
                        items.append((key, value))

                items += event_dict.items()

                return items

        elif sort_keys:

            def ordered_items(event_dict: EventDict) -> List[Tuple[str, Any]]:
                return sorted(event_dict.items())

        else:
            ordered_items = operator.methodcaller("items")

        self._ordered_items = ordered_items

        if repr_native_str is True:
            self._repr = repr
        else:

            def _repr(inst: Any) -> str:
                if isinstance(inst, str):
                    return inst
                else:
                    return repr(inst)

            self._repr = _repr

    def __call__(
        self, _: WrappedLogger, __: str, event_dict: EventDict
    ) -> str:
        return " ".join(
            k + "=" + self._repr(v) for k, v in self._ordered_items(event_dict)
        )


class UnicodeEncoder:
    """
    Encode unicode values in ``event_dict``.

    :param encoding: Encoding to encode to (default: ``"utf-8"``).
    :param errors: How to cope with encoding errors (default
        ``"backslashreplace"``).

    Useful if you're running Python 2 as otherwise ``u"abc"`` will be rendered
    as ``'u"abc"'``.

    Just put it in the processor chain before the renderer.
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

    :param encoding: Encoding to decode from (default: ``"utf-8"``).
    :param errors: How to cope with encoding errors (default:
        ``"replace"``).

    Useful if you're running Python 3 as otherwise ``b"abc"`` will be rendered
    as ``'b"abc"'``.

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
    Render the ``event_dict`` using ``serializer(event_dict, **json_kw)``.

    :param json_kw: Are passed unmodified to *serializer*.  If *default*
        is passed, it will disable support for ``__structlog__``-based
        serialization.
    :param serializer: A :func:`json.dumps`-compatible callable that
        will be used to format the string.  This can be used to use alternative
        JSON encoders like `simplejson
        <https://pypi.org/project/simplejson/>`_ or `RapidJSON
        <https://pypi.org/project/python-rapidjson/>`_ (faster but Python
        3-only) (default: :func:`json.dumps`).

    .. versionadded:: 0.2.0
        Support for ``__structlog__`` serialization method.

    .. versionadded:: 15.4.0
        *serializer* parameter.

    .. versionadded:: 18.2.0
       Serializer's *default* parameter can be overwritten now.

    """

    def __init__(
        self,
        serializer: Callable[..., Union[str, bytes]] = json.dumps,
        **dumps_kw: Any
    ) -> None:
        dumps_kw.setdefault("default", _json_fallback_handler)
        self._dumps_kw = dumps_kw
        self._dumps = serializer

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> Union[str, bytes]:
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
    else:
        try:
            return obj.__structlog__()
        except AttributeError:
            return repr(obj)


def format_exc_info(
    logger: WrappedLogger, name: str, event_dict: EventDict
) -> EventDict:
    """
    Replace an ``exc_info`` field by an ``exception`` string field:

    If *event_dict* contains the key ``exc_info``, there are two possible
    behaviors:

    - If the value is a tuple, render it into the key ``exception``.
    - If the value is an Exception *and* you're running Python 3, render it
      into the key ``exception``.
    - If the value true but no tuple, obtain exc_info ourselves and render
      that.

    If there is no ``exc_info`` key, the *event_dict* is not touched.
    This behavior is analogue to the one of the stdlib's logging.
    """
    exc_info = event_dict.pop("exc_info", None)
    if exc_info:
        event_dict["exception"] = _format_exception(
            _figure_out_exc_info(exc_info)
        )

    return event_dict


class TimeStamper:
    """
    Add a timestamp to ``event_dict``.

    :param fmt: strftime format string, or ``"iso"`` for `ISO 8601
        <https://en.wikipedia.org/wiki/ISO_8601>`_, or `None` for a `UNIX
        timestamp <https://en.wikipedia.org/wiki/Unix_time>`_.
    :param utc: Whether timestamp should be in UTC or local time.
    :param key: Target key in *event_dict* for added timestamps.

    .. versionchanged:: 19.2 Can be pickled now.
    """

    __slots__ = ("_stamper", "fmt", "utc", "key")

    def __init__(
        self,
        fmt: Optional[str] = None,
        utc: bool = True,
        key: str = "timestamp",
    ) -> None:
        self.fmt, self.utc, self.key = fmt, utc, key

        self._stamper = _make_stamper(fmt, utc, key)

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> EventDict:
        return self._stamper(event_dict)

    def __getstate__(self) -> Dict[str, Any]:
        return {"fmt": self.fmt, "utc": self.utc, "key": self.key}

    def __setstate__(self, state: Dict[str, Any]) -> None:
        self.fmt = state["fmt"]
        self.utc = state["utc"]
        self.key = state["key"]

        self._stamper = _make_stamper(**state)


def _make_stamper(
    fmt: Optional[str], utc: bool, key: str
) -> Callable[[EventDict], EventDict]:
    """
    Create a stamper function.
    """
    if fmt is None and not utc:
        raise ValueError("UNIX timestamps are always UTC.")

    now = getattr(datetime.datetime, "utcnow" if utc else "now")

    if fmt is None:

        def stamper_unix(event_dict: EventDict) -> EventDict:
            event_dict[key] = time.time()

            return event_dict

        return stamper_unix
    elif fmt.upper() == "ISO":

        def stamper_iso_local(event_dict: EventDict) -> EventDict:
            event_dict[key] = now().isoformat()
            return event_dict

        def stamper_iso_utc(event_dict: EventDict) -> EventDict:
            event_dict[key] = now().isoformat() + "Z"
            return event_dict

        if utc:
            return stamper_iso_utc
        else:
            return stamper_iso_local

    def stamper_fmt(event_dict: EventDict) -> EventDict:
        event_dict[key] = now().strftime(fmt)

        return event_dict

    return stamper_fmt


def _figure_out_exc_info(v: Any) -> ExcInfo:
    """
    Depending on the Python version will try to do the smartest thing possible
    to transform *v* into an ``exc_info`` tuple.
    """
    if isinstance(v, BaseException):
        return (v.__class__, v, v.__traceback__)
    elif isinstance(v, tuple):
        return v  # type: ignore
    elif v:
        return sys.exc_info()  # type: ignore

    return v


class ExceptionPrettyPrinter:
    """
    Pretty print exceptions and remove them from the ``event_dict``.

    :param file: Target file for output (default: ``sys.stdout``).

    This processor is mostly for development and testing so you can read
    exceptions properly formatted.

    It behaves like format_exc_info` except it removes the exception
    data from the event dictionary after printing it.

    It's tolerant to having `format_exc_info` in front of itself in the
    processor chain but doesn't require it.  In other words, it handles both
    ``exception`` as well as ``exc_info`` keys.

    .. versionadded:: 0.4.0

    .. versionchanged:: 16.0.0
       Added support for passing exceptions as ``exc_info`` on Python 3.
    """

    def __init__(self, file: Optional[TextIO] = None) -> None:
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
                exc = _format_exception(exc_info)

        if exc:
            print(exc, file=self._file)

        return event_dict


class StackInfoRenderer:
    """
    Add stack information with key ``stack`` if ``stack_info`` is `True`.

    Useful when you want to attach a stack dump to a log entry without
    involving an exception.

    It works analogously to the *stack_info* argument of the Python 3 standard
    library logging but works on both 2 and 3.

    .. versionadded:: 0.4.0
    """

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> EventDict:
        if event_dict.pop("stack_info", None):
            event_dict["stack"] = _format_stack(
                _find_first_app_frame_and_name()[0]
            )

        return event_dict
