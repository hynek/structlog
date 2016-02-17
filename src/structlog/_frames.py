# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import absolute_import, division, print_function

import sys
import traceback

from six.moves import cStringIO as StringIO


def _format_exception(exc_info):
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
    while any(name.startswith(i) for i in ignores):
        if f.f_back is None:
            name = "?"
            break
        f = f.f_back
        name = f.f_globals.get("__name__") or "?"
    return f, name


def _format_stack(frame):
    """
    Pretty-print the stack of `frame` like logging would.
    """
    sio = StringIO()
    sio.write('Stack (most recent call last):\n')
    traceback.print_stack(frame, file=sio)
    sinfo = sio.getvalue()
    if sinfo[-1] == '\n':
        sinfo = sinfo[:-1]
    sio.close()
    return sinfo
