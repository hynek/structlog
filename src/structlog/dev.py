# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Helpers that make development with ``structlog`` more pleasant.
"""

from __future__ import absolute_import, division, print_function

from six import StringIO

try:
    import colorama
except ImportError:
    colorama = None


__all__ = [
    "ConsoleRenderer",
]


_MISSING = (
    "{who} requires the {package} package installed.  "
    "If you want to use the helpers from structlog.dev, it is strongly "
    "recommended to install structlog using `pip install structlog[dev]`."
)
_EVENT_WIDTH = 30  # pad the event name to so many characters


def _pad(s, l):
    """
    Pads *s* to length *l*.
    """
    missing = l - len(s)
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

    RESET_ALL = BRIGHT = DIM = RED = BLUE = CYAN = MAGENTA = YELLOW = GREEN = \
        RED_BACK = ""


class _ColorfulStyles(object):
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


class _PlainStyles(object):
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


class ConsoleRenderer(object):
    """
    Render `event_dict` nicely aligned, possibly in colors, and ordered.

    :param int pad_event: Pad the event to this many characters.
    :param bool colors: Use colors for a nicer output.

    Requires the colorama_ package if *colors* is ``True``.

    .. _colorama: https://pypi.org/project/colorama/

    .. versionadded:: 16.0
    .. versionadded:: 16.1 *colors* argument
    """
    def __init__(self, pad_event=_EVENT_WIDTH, colors=True):
        if colors is True:
            if colorama is None:
                raise SystemError(
                    _MISSING.format(
                        who=self.__class__.__name__ + " with `colors=True`",
                        package="colorama"
                    )
                )

            colorama.init()
            styles = _ColorfulStyles
        else:
            styles = _PlainStyles

        self._styles = styles
        self._pad_event = pad_event
        self._level_to_color = {
            "critical": styles.level_critical,
            "exception": styles.level_exception,
            "error": styles.level_error,
            "warn": styles.level_warn,
            "warning": styles.level_warn,
            "info": styles.level_info,
            "debug": styles.level_debug,
            "notset": styles.level_notset,
        }

        for key in self._level_to_color.keys():
            self._level_to_color[key] += styles.bright
        self._longest_level = len(max(
            self._level_to_color.keys(),
            key=lambda e: len(e)
        ))

    def __call__(self, _, __, event_dict):
        sio = StringIO()

        ts = event_dict.pop("timestamp", None)
        if ts is not None:
            sio.write(
                # can be a number if timestamp is UNIXy
                self._styles.timestamp + str(ts) + self._styles.reset + " "
            )
        level = event_dict.pop("level",  None)
        if level is not None:
            sio.write(
                "[" + self._level_to_color[level] +
                _pad(level, self._longest_level) +
                self._styles.reset + "] "
            )

        event = event_dict.pop("event")
        if event_dict:
            event = _pad(event, self._pad_event) + self._styles.reset + " "
        else:
            event += self._styles.reset
        sio.write(self._styles.bright + event)

        logger_name = event_dict.pop("logger", None)
        if logger_name is not None:
            sio.write(
                "[" + self._styles.logger_name + self._styles.bright +
                logger_name + self._styles.reset +
                "] "
            )

        stack = event_dict.pop("stack", None)
        exc = event_dict.pop("exception", None)
        sio.write(
            " ".join(
                self._styles.kv_key + key + self._styles.reset +
                "=" +
                self._styles.kv_value + repr(event_dict[key]) +
                self._styles.reset
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
