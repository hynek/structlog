# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import asyncio
import multiprocessing
import sys

from types import SimpleNamespace
from unittest.mock import patch

from structlog._utils import get_processname, get_taskname


class TestGetProcessname:
    def test_default(self):
        """
        The returned process name matches the name of the current process from
        the `multiprocessing` module.
        """
        assert get_processname() == multiprocessing.current_process().name

    def test_changed(self):
        """
        The returned process name matches the name of the current process from
        the `multiprocessing` module if it is not the default.
        """
        tmp_name = "fakename"

        with patch.object(
            multiprocessing,
            "current_process",
            lambda: SimpleNamespace(name=tmp_name),
        ):
            actual = get_processname()

        assert tmp_name == actual

    def test_no_multiprocessing(self) -> None:
        """
        The returned process name is the default process name if the
        `multiprocessing` module is not available.
        """
        with patch.object(sys, "modules", {}):
            actual = get_processname()

        assert "n/a" == actual

    def test_exception(self) -> None:
        """
        The returned process name is the default process name when an exception
        is thrown when an attempt is made to retrieve the current process name
        from the `multiprocessing` module.
        """

        def _current_process() -> None:
            raise RuntimeError("test")

        with patch.object(
            multiprocessing, "current_process", _current_process
        ):
            actual = get_processname()

        assert "n/a" == actual


class TestGetTaskname:
    def test_no_task(self) -> None:
        """
        The task name is None if there is no running asyncio task.
        """
        assert get_taskname() is None

    async def test_named_task(self) -> None:
        """
        The task name is the name of the running asyncio task.
        """

        async def _get_taskname() -> str | None:
            return get_taskname()

        task = asyncio.create_task(_get_taskname())
        task.set_name("test-task")

        assert "test-task" == await task
        assert get_taskname() == asyncio.current_task().get_name()

    def test_no_asyncio(self) -> None:
        """
        The task name is None if the `asyncio` module is not available.
        """
        with patch.object(sys, "modules", {}):
            actual = get_taskname()

        assert actual is None

    def test_exception(self) -> None:
        """
        The task name is None when an exception is thrown when an attempt
        is made to retrieve the current task.
        """

        def _current_task() -> None:
            raise RuntimeError("test")

        with patch.object(asyncio, "current_task", _current_task):
            actual = get_taskname()

        assert actual is None
