# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import absolute_import, division, print_function

import sys
import traceback

from types import FrameType
from typing import TYPE_CHECKING, List, Optional, Tuple, cast

from six.moves import cStringIO as StringIO


if TYPE_CHECKING:
    import logging


def _format_exception(exc_info):
    # type: (logging._SysExcInfoType) -> str
    """
    Prettyprint an `exc_info` tuple.

    Shamelessly stolen from stdlib's logging module.
    """
    sio = StringIO()
    traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], None, sio)
    s = sio.getvalue()
    sio.close()
    if s[-1:] == "\n":
        s = s[:-1]
    return s


def _find_first_app_frame_and_name(additional_ignores=None):
    # type: (Optional[List[str]]) -> Tuple[FrameType, str]
    """
    Remove all intra-structlog calls and return the relevant app frame.

    :param additional_ignores: Additional names with which the first frame must
        not start.
    :type additional_ignores: `list` of `str` or `None`

    :rtype: tuple of (frame, name)
    """
    ignores = ["structlog"] + (additional_ignores or [])
    f = sys._getframe()
    name = f.f_globals.get("__name__") or "?"
    while any(tuple(name.startswith(i) for i in ignores)):
        if f.f_back is None:
            name = "?"  # type: ignore
            break
        f = f.f_back
        name = f.f_globals.get("__name__") or "?"
    return f, cast(str, name)


def _format_stack(frame):
    # type: (FrameType) -> str
    """
    Pretty-print the stack of `frame` like logging would.
    """
    sio = StringIO()
    sio.write("Stack (most recent call last):\n")
    traceback.print_stack(frame, file=sio)
    sinfo = sio.getvalue()
    if sinfo[-1] == "\n":
        sinfo = sinfo[:-1]
    sio.close()
    return sinfo
