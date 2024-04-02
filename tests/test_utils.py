# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import multiprocessing
import sys

import pytest

from structlog._utils import get_processname


class TestGetProcessname:
    def test_default(self):
        """
        The returned process name matches the name of the current process from
        the `multiprocessing` module.
        """
        assert get_processname() == multiprocessing.current_process().name

    def test_changed(self, monkeypatch: pytest.MonkeyPatch):
        """
        The returned process name matches the name of the current process from
        the `multiprocessing` module if it is not the default.
        """
        tmp_name = "fakename"
        monkeypatch.setattr(
            target=multiprocessing.current_process(),
            name="name",
            value=tmp_name,
        )

        assert get_processname() == tmp_name

    def test_no_multiprocessing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        The returned process name is the default process name if the
        `multiprocessing` module is not available.
        """
        tmp_name = "fakename"
        monkeypatch.setattr(
            target=multiprocessing.current_process(),
            name="name",
            value=tmp_name,
        )
        monkeypatch.setattr(
            target=sys,
            name="modules",
            value={},
        )

        assert get_processname() == "n/a"

    def test_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        The returned process name is the default process name when an exception
        is thrown when an attempt is made to retrieve the current process name
        from the `multiprocessing` module.
        """

        def _current_process() -> None:
            raise RuntimeError("test")

        monkeypatch.setattr(
            target=multiprocessing,
            name="current_process",
            value=_current_process,
        )

        assert get_processname() == "n/a"
