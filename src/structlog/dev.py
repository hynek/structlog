# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Helpers that aim to make development with ``structlog`` more pleasant.
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
    RESET_ALL = colorama.Style.RESET_ALL
    BRIGHT = colorama.Style.BRIGHT
    DIM = colorama.Style.DIM
    RED = colorama.Fore.RED
    BLUE = colorama.Fore.BLUE
    CYAN = colorama.Fore.CYAN
    MAGENTA = colorama.Fore.MAGENTA
    YELLOW = colorama.Fore.YELLOW
    GREEN = colorama.Fore.GREEN


class ConsoleRenderer(object):
    """
    Render `event_dict` nicely aligned, in colors, and ordered.

    :param int pad_event: Pad the event to this many characters.

    Requires the colorama_ package.

    .. _colorama: https://pypi.python.org/pypi/colorama/

    .. versionadded:: 16.0.0
    """
    def __init__(self, pad_event=_EVENT_WIDTH):
        if colorama is None:
            raise SystemError(
                _MISSING.format(
                    who=self.__class__.__name__,
                    package="colorama"
                )
            )
        colorama.init()

        self._pad_event = pad_event
        self._level_to_color = {
            "critical": RED,
            "exception": RED,
            "error": RED,
            "warn": YELLOW,
            "warning": YELLOW,
            "info": GREEN,
            "debug": GREEN,
            "notset": colorama.Back.RED,
        }
        for key in self._level_to_color.keys():
            self._level_to_color[key] += BRIGHT
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
                DIM + str(ts) + RESET_ALL + " "
            )
        level = event_dict.pop("level",  None)
        if level is not None:
            sio.write(
                "[" + self._level_to_color[level] +
                _pad(level, self._longest_level) +
                RESET_ALL + "] "
            )

        sio.write(
            BRIGHT +
            _pad(event_dict.pop("event"), self._pad_event) +
            RESET_ALL + " "
        )

        logger_name = event_dict.pop("logger", None)
        if logger_name is not None:
            sio.write(
                "[" + BLUE + BRIGHT +
                logger_name + RESET_ALL +
                "] "
            )

        stack = event_dict.pop("stack", None)
        exc = event_dict.pop("exception", None)
        sio.write(
            " ".join(
                CYAN + key + RESET_ALL +
                "=" +
                MAGENTA + repr(event_dict[key]) +
                RESET_ALL
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
