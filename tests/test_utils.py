# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import errno
import multiprocessing
import sys

import pytest

from pretend import raiser

from structlog._utils import get_processname, until_not_interrupted


class TestUntilNotInterrupted:
    def test_passes_arguments_and_returns_return_value(self):
        def returner(*args, **kw):
            return args, kw

        assert ((42,), {"x": 23}) == until_not_interrupted(returner, 42, x=23)

    def test_leaves_unrelated_exceptions_through(self):
        exc = IOError
        with pytest.raises(exc):
            until_not_interrupted(raiser(exc("not EINTR")))

    def test_retries_on_EINTR(self):
        calls = [0]

        def raise_on_first_three():
            if calls[0] < 3:
                calls[0] += 1
                raise OSError(errno.EINTR)

        until_not_interrupted(raise_on_first_three)

        assert 3 == calls[0]


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
