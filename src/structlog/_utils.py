# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Generic utilities.
"""

from __future__ import annotations


__lazy_modules__ = ["contextlib"]

import sys

from contextlib import suppress
from typing import Any


def get_processname() -> str:
    # based on code from
    # https://github.com/python/cpython/blob/313f92a57bc3887026ec16adb536bb2b7580ce47/Lib/logging/__init__.py#L342-L352
    processname = "n/a"
    mp: Any = sys.modules.get("multiprocessing")
    if mp is not None:
        # Errors may occur if multiprocessing has not finished loading
        # yet - e.g. if a custom import hook causes third-party code
        # to run when multiprocessing calls import.
        with suppress(Exception):
            processname = mp.current_process().name

    return processname


def get_taskname() -> str | None:
    """
    Get the name of the current asyncio task, if any.

    Returns `None` if there is no running task -- for example, because the
    code is not running in an event loop at all.
    """
    # `asyncio` is only looked up, never imported, mirroring
    # `get_processname` above: if it has not been imported yet, no task can
    # be running.
    task_name = None
    aio: Any = sys.modules.get("asyncio")
    if aio is not None:
        # Errors may occur if asyncio has not finished loading yet, and
        # `asyncio.current_task()` raises `RuntimeError` if there is no
        # running event loop.
        with suppress(Exception):
            task = aio.current_task()
            task_name = task.get_name() if task is not None else None

    return task_name
