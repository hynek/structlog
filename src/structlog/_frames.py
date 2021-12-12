# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import inspect
import sys
import traceback

from io import StringIO
from types import FrameType
from typing import List, Optional, Tuple

from .types import ExcInfo


def _format_exception(exc_info: ExcInfo) -> str:
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


def _find_first_app_frame_and_name(
    additional_ignores: Optional[List[str]] = None,
) -> Tuple[FrameType, str]:
    """
    Remove all intra-structlog calls and return the relevant app frame.

    :param additional_ignores: Additional names with which the first frame must
        not start.

    :returns: tuple of (frame, name)
    """
    ignores = ["structlog"] + (additional_ignores or [])
    f = sys._getframe()
    traceback.print_stack()
    sys.stderr.write(f"_find_first_app_frame_and_name: f={f}\n")
    sys.stderr.write(f"_find_first_app_frame_and_name: f.f_back={f.f_back}\n")
    # sys.stderr.write(f"_find_first_app_frame_and_name: f.f_globals={f.f_globals}\n")
    name = f.f_globals.get("__name__") or "?"
    sys.stderr.write(f"_find_first_app_frame_and_name: name={name}, f = {f}, f.f_code = {f.f_code}\n")
    sys.stderr.write(f"_find_first_app_frame_and_name: ignores={ignores}\n")

    # sys.stderr.write(f"name={name}\n")
    while any(tuple(name.startswith(i) for i in ignores)):
        # sys.stderr.write(f"name={name}\n")
        if f.f_back is None:
            name = "?"
            break
        f = f.f_back
        name = f.f_globals.get("__name__") or "?"
        sys.stderr.write(f"_find_first_app_frame_and_name: name={name}, f = {f}, f.f_code = {f.f_code}\n")
    # sys.stderr.write(f"f = {f}, name={name}\n")
    # traceback.print_stack()
    sys.stderr.write(f"_find_first_app_frame_and_name: f={f}, name={name}\n")
    return f, name


def _format_stack(frame: FrameType) -> str:
    """
    Pretty-print the stack of *frame* like logging would.
    """
    sio = StringIO()

    sio.write("Stack (most recent call last):\n")
    traceback.print_stack(frame, file=sio)
    sinfo = sio.getvalue()
    if sinfo[-1] == "\n":
        sinfo = sinfo[:-1]
    sio.close()

    return sinfo
