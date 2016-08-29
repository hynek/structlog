# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Helpers that aim to make development with ``structlog`` more pleasant.
"""

from __future__ import absolute_import, division, print_function

import warnings

from six import StringIO

try:
    import colorama
except ImportError:
    colorama = None

__all__ = [
    "ConsoleRenderer",
]


_MISSING = (
    "{who} requires the {package} package installed to use colors.  "
    "If you want to use the helpers from structlog.dev with colors, "
    "it is strongly recommended to install structlog using "
    "`pip install structlog[dev]`."
)
_EVENT_WIDTH = 30  # pad the event name to so many characters


def _pad(s, l):
    """
    Pads *s* to length *l*.
    """
    missing = l - len(s)
    return s + " " * (missing if missing > 0 else 0)


NO_COLOR = ''
RESET_ALL = colorama.Style.RESET_ALL if colorama else NO_COLOR
BRIGHT = colorama.Style.BRIGHT if colorama else NO_COLOR
DIM = colorama.Style.DIM if colorama else NO_COLOR
RED = colorama.Fore.RED if colorama else NO_COLOR
BLUE = colorama.Fore.BLUE if colorama else NO_COLOR
CYAN = colorama.Fore.CYAN if colorama else NO_COLOR
MAGENTA = colorama.Fore.MAGENTA if colorama else NO_COLOR
YELLOW = colorama.Fore.YELLOW if colorama else NO_COLOR
GREEN = colorama.Fore.GREEN if colorama else NO_COLOR
NOT_SET = colorama.Back.RED if colorama else NO_COLOR


class ConsoleRenderer(object):
    """
    Render `event_dict` nicely aligned, in colors, and ordered.

    :param int pad_event: Pad the event to this many characters.
    :param bool colors: Colorize output or not.

    Requires the colorama_ package for setting colors=True.

    .. _colorama: https://pypi.python.org/pypi/colorama/

    .. versionadded:: 16.0.0
    """
    def __init__(self, pad_event=_EVENT_WIDTH, colors=True):
        if colors:
            if colorama is None:
                warnings.warn(_MISSING.format(who=self.__class__.__name__,
                                              package="colorama"),
                              RuntimeWarning)
            else:
                colorama.init()

        self._pad_event = pad_event
        self._colors = bool(colorama and colors)
        self._level_to_color = {
            "critical": RED,
            "exception": RED,
            "error": RED,
            "warn": YELLOW,
            "warning": YELLOW,
            "info": GREEN,
            "debug": GREEN,
            "notset": NOT_SET,
        }
        for key in self._level_to_color.keys():
            self._level_to_color[key] += BRIGHT
        self._longest_level = len(max(
            self._level_to_color.keys(),
            key=lambda e: len(e)
        ))

    def _filter_color(self, color):
        return color if self._colors else ''

    def __call__(self, _, __, event_dict):
        sio = StringIO()

        ts = event_dict.pop("timestamp", None)
        if ts is not None:
            sio.write(
                # can be a number if timestamp is UNIXy
                self._filter_color(DIM) +
                str(ts) +
                self._filter_color(RESET_ALL) + " "
            )
        level = event_dict.pop("level",  None)
        if level is not None:
            sio.write(
                "[" + self._filter_color(self._level_to_color[level]) +
                _pad(level, self._longest_level) +
                self._filter_color(RESET_ALL) + "] "
            )

        sio.write(
            self._filter_color(BRIGHT) +
            _pad(event_dict.pop("event"), self._pad_event) +
            self._filter_color(RESET_ALL) + " "
        )

        logger_name = event_dict.pop("logger", None)
        if logger_name is not None:
            sio.write(
                "[" + self._filter_color(BLUE + BRIGHT) +
                logger_name + self._filter_color(RESET_ALL) +
                "] "
            )

        stack = event_dict.pop("stack", None)
        exc = event_dict.pop("exception", None)
        sio.write(
            " ".join(
                self._filter_color(CYAN) + key +
                self._filter_color(RESET_ALL) +
                "=" +
                self._filter_color(MAGENTA) + repr(event_dict[key]) +
                self._filter_color(RESET_ALL)
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
