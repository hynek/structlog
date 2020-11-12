# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Helpers that make development with ``structlog`` more pleasant.
"""

import sys

from io import StringIO
from typing import Any, Optional, Type, Union

from .types import EventDict, Protocol, WrappedLogger


try:
    import colorama
except ImportError:
    colorama = None


__all__ = ["ConsoleRenderer"]

_IS_WINDOWS = sys.platform == "win32"

_MISSING = "{who} requires the {package} package installed.  "
_EVENT_WIDTH = 30  # pad the event name to so many characters


def _pad(s: str, length: int) -> str:
    """
    Pads *s* to length *lenght*.
    """
    missing = length - len(s)

    return s + " " * (missing if missing > 0 else 0)


if colorama is not None:
    _has_colorama = True

    RESET_ALL = colorama.Style.RESET_ALL
    BRIGHT = colorama.Style.BRIGHT
    DIM = colorama.Style.DIM
    RED = colorama.Fore.RED
    BLUE = colorama.Fore.BLUE
    CYAN = colorama.Fore.CYAN
    MAGENTA = colorama.Fore.MAGENTA
    YELLOW = colorama.Fore.YELLOW
    GREEN = colorama.Fore.GREEN
    RED_BACK = colorama.Back.RED
else:
    _has_colorama = False

    RESET_ALL = (
        BRIGHT
    ) = DIM = RED = BLUE = CYAN = MAGENTA = YELLOW = GREEN = RED_BACK = ""


class _Styles(Protocol):
    reset: str
    bright: str
    level_critical: str
    level_exception: str
    level_error: str
    level_warn: str
    level_info: str
    level_debug: str
    level_notset: str

    timestamp: str
    logger_name: str
    kv_key: str
    kv_value: str


Styles = Union[_Styles, Type[_Styles]]


class _ColorfulStyles:
    reset = RESET_ALL
    bright = BRIGHT

    level_critical = RED
    level_exception = RED
    level_error = RED
    level_warn = YELLOW
    level_info = GREEN
    level_debug = GREEN
    level_notset = RED_BACK

    timestamp = DIM
    logger_name = BLUE
    kv_key = CYAN
    kv_value = MAGENTA


class _PlainStyles:
    reset = ""
    bright = ""

    level_critical = ""
    level_exception = ""
    level_error = ""
    level_warn = ""
    level_info = ""
    level_debug = ""
    level_notset = ""

    timestamp = ""
    logger_name = ""
    kv_key = ""
    kv_value = ""


class ConsoleRenderer:
    """
    Render ``event_dict`` nicely aligned, possibly in colors, and ordered.

    If ``event_dict`` contains an ``exception`` key (for example from
    :func:`~structlog.processors.format_exc_info`), it will be rendered *after*
    the log line.

    :param pad_event: Pad the event to this many characters.
    :param colors: Use colors for a nicer output.
    :param force_colors: Force colors even for non-tty destinations.
        Use this option if your logs are stored in a file that is meant
        to be streamed to the console.
    :param repr_native_str: When `True`, `repr` is also applied
        to native strings (i.e. unicode on Python 3 and bytes on Python 2).
        Setting this to `False` is useful if you want to have human-readable
        non-ASCII output on Python 2.  The ``event`` key is *never*
        `repr` -ed.
    :param level_styles: When present, use these styles for colors. This
        must be a dict from level names (strings) to colorama styles. The
        default can be obtained by calling
        `ConsoleRenderer.get_default_level_styles`

    Requires the colorama_ package if *colors* is `True`.

    .. _colorama: https://pypi.org/project/colorama/

    .. versionadded:: 16.0
    .. versionadded:: 16.1 *colors*
    .. versionadded:: 17.1 *repr_native_str*
    .. versionadded:: 18.1 *force_colors*
    .. versionadded:: 18.1 *level_styles*
    .. versionchanged:: 19.2
       ``colorama`` now initializes lazily to avoid unwanted initializations as
       ``ConsoleRenderer`` is used by default.
    .. versionchanged:: 19.2 Can be pickled now.
    .. versionchanged:: 20.1 ``colorama`` does not initialize lazily on Windows
       anymore because it breaks rendering.
    """

    def __init__(
        self,
        pad_event: int = _EVENT_WIDTH,
        colors: bool = _has_colorama,
        force_colors: bool = False,
        repr_native_str: bool = False,
        level_styles: Optional[Styles] = None,
    ):
        self._force_colors = self._init_colorama = False
        styles: Styles
        if colors is True:
            if colorama is None:
                raise SystemError(
                    _MISSING.format(
                        who=self.__class__.__name__ + " with `colors=True`",
                        package="colorama",
                    )
                )

            if _IS_WINDOWS:  # pragma: no cover
                _init_colorama(self._force_colors)
            else:
                self._init_colorama = True
                if force_colors:
                    self._force_colors = True

            styles = _ColorfulStyles
        else:
            styles = _PlainStyles

        self._styles = styles
        self._pad_event = pad_event

        if level_styles is None:
            self._level_to_color = self.get_default_level_styles(colors)
        else:
            self._level_to_color = level_styles

        for key in self._level_to_color.keys():
            self._level_to_color[key] += styles.bright
        self._longest_level = len(
            max(self._level_to_color.keys(), key=lambda e: len(e))
        )

        self._repr_native_str = repr_native_str

    def _repr(self, val: Any) -> str:
        """
        Determine representation of *val* depending on its type &
        self._repr_native_str.
        """
        if self._repr_native_str is True:
            return repr(val)

        if isinstance(val, str):
            return val
        else:
            return repr(val)

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> str:

        # Initialize lazily to prevent import side-effects.
        if self._init_colorama:
            _init_colorama(self._force_colors)
            self._init_colorama = False
        sio = StringIO()

        ts = event_dict.pop("timestamp", None)
        if ts is not None:
            sio.write(
                # can be a number if timestamp is UNIXy
                self._styles.timestamp
                + str(ts)
                + self._styles.reset
                + " "
            )
        level = event_dict.pop("level", None)
        if level is not None:
            sio.write(
                "["
                + self._level_to_color[level]
                + _pad(level, self._longest_level)
                + self._styles.reset
                + "] "
            )

        # force event to str for compatibility with standard library
        event = event_dict.pop("event", None)
        if not isinstance(event, str):
            event = str(event)

        if event_dict:
            event = _pad(event, self._pad_event) + self._styles.reset + " "
        else:
            event += self._styles.reset
        sio.write(self._styles.bright + event)

        logger_name = event_dict.pop("logger", None)
        if logger_name is not None:
            sio.write(
                "["
                + self._styles.logger_name
                + self._styles.bright
                + logger_name
                + self._styles.reset
                + "] "
            )

        stack = event_dict.pop("stack", None)
        exc = event_dict.pop("exception", None)
        sio.write(
            " ".join(
                self._styles.kv_key
                + key
                + self._styles.reset
                + "="
                + self._styles.kv_value
                + self._repr(event_dict[key])
                + self._styles.reset
                for key in sorted(event_dict.keys())
            )
        )

        if stack is not None:
            sio.write("\n" + stack)
            if exc is not None:
                sio.write("\n\n" + "=" * 79 + "\n")
        if exc is not None:
            sio.write("\n" + exc)

        return sio.getvalue()

    @staticmethod
    def get_default_level_styles(colors: bool = True) -> Any:
        """
        Get the default styles for log levels

        This is intended to be used with `ConsoleRenderer`'s ``level_styles``
        parameter.  For example, if you are adding custom levels in your
        home-grown :func:`~structlog.stdlib.add_log_level` you could do::

            my_styles = ConsoleRenderer.get_default_level_styles()
            my_styles["EVERYTHING_IS_ON_FIRE"] = my_styles["critical"]
            renderer = ConsoleRenderer(level_styles=my_styles)

        :param colors: Whether to use colorful styles. This must match the
            *colors* parameter to `ConsoleRenderer`. Default: `True`.
        """
        styles: Styles
        if colors:
            styles = _ColorfulStyles
        else:
            styles = _PlainStyles
        return {
            "critical": styles.level_critical,
            "exception": styles.level_exception,
            "error": styles.level_error,
            "warn": styles.level_warn,
            "warning": styles.level_warn,
            "info": styles.level_info,
            "debug": styles.level_debug,
            "notset": styles.level_notset,
        }


def _init_colorama(force: bool) -> None:
    if force:
        colorama.deinit()
        colorama.init(strip=False)
    else:
        colorama.init()


_SENTINEL = object()


def set_exc_info(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:

    """
    Set ``event_dict["exc_info"] = True`` if *method_name* is ``"exception"``.

    Do nothing if the name is different or ``exc_info`` is already set.
    """
    if (
        method_name != "exception"
        or event_dict.get("exc_info", _SENTINEL) is not _SENTINEL
    ):
        return event_dict

    event_dict["exc_info"] = True

    return event_dict
