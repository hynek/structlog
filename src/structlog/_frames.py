# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import annotations

import inspect
import sys
import traceback

from io import StringIO
from types import FrameType

from .contextvars import _ASYNC_CALLING_STACK
from .typing import ExcInfo


def _format_exception(exc_info: ExcInfo) -> str:
    """
    Prettyprint an `exc_info` tuple.

    Shamelessly stolen from stdlib's logging module.
    """
    if exc_info == (None, None, None):  # type: ignore[comparison-overlap]
        return "MISSING"

    sio = StringIO()

    traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], None, sio)
    s = sio.getvalue()
    sio.close()
    if s[-1:] == "\n":
        s = s[:-1]

    return s


def _find_first_app_frame_and_name(
    additional_ignores: list[str] | None = None,
) -> tuple[FrameType, str]:
    """
    Remove all intra-structlog calls and return the relevant app frame.

    Arguments:

        additional_ignores:
            Additional names with which the first frame must not start.

    Returns:

        tuple of (frame, name)
    """
    ignores = ["structlog"] + (additional_ignores or [])
    f = _ASYNC_CALLING_STACK.get(sys._getframe())
    name = f.f_globals.get("__name__") or "?"
    while any(tuple(name.startswith(i) for i in ignores)):
        if f.f_back is None:
            name = "?"
            break
        f = f.f_back
        name = f.f_globals.get("__name__") or "?"
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


def _get_qual_name(frame: FrameType) -> str:
    """
    For a given app frame, attempt to deduce the namespace
    by crawling through the frame's ``f_globals`` to find
    matching object code.

    This O(n) procedure should return as O(1) in most situations,
    but buyer beware.

    Arguments:

        frame:
            Frame to process.

    Returns:

        string of the deduced namespace

    .. versionadded:: 23.3.0
    """
    identified_namespace = frame.f_code.co_name

    for cls in {
        obj for obj in frame.f_globals.values() if inspect.isclass(obj)
    }:
        member = getattr(cls, frame.f_code.co_name, None)
        # store the current namespace as a fall back (probably the namespace)
        identified_namespace = f"{cls.__module__}.{frame.f_code.co_name}"
        if inspect.isfunction(member) and member.__code__ == frame.f_code:
            # we found our code match, can stop looking
            """identified_namespace = f"{member.__module__}.{member.__qualname__}" """
            return f"{member.__module__}.{member.__qualname__}"

    return identified_namespace
