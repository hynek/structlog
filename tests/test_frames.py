# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import absolute_import, division, print_function

import sys

import pytest

from pretend import stub

import structlog._frames

from structlog._frames import (
    _find_first_app_frame_and_name,
    _format_exception,
    _format_stack,
)


class TestFindFirstAppFrameAndName(object):
    def test_ignores_structlog_by_default(self, monkeypatch):
        """
        No matter what you pass in, structlog frames get always ignored.
        """
        f1 = stub(f_globals={'__name__': 'test'}, f_back=None)
        f2 = stub(f_globals={'__name__': 'structlog.blubb'}, f_back=f1)
        monkeypatch.setattr(structlog._frames.sys, '_getframe', lambda: f2)
        f, n = _find_first_app_frame_and_name()
        assert ((f1, 'test') == (f, n))

    def test_ignoring_of_additional_frame_names_works(self, monkeypatch):
        """
        Additional names are properly ignored too.
        """
        f1 = stub(f_globals={'__name__': 'test'}, f_back=None)
        f2 = stub(f_globals={'__name__': 'ignored.bar'}, f_back=f1)
        f3 = stub(f_globals={'__name__': 'structlog.blubb'}, f_back=f2)
        monkeypatch.setattr(structlog._frames.sys, '_getframe', lambda: f3)
        f, n = _find_first_app_frame_and_name(additional_ignores=['ignored'])
        assert ((f1, 'test') == (f, n))

    def test_tolerates_missing_name(self, monkeypatch):
        """
        Use ``?`` if `f_globals` lacks a `__name__` key
        """
        f1 = stub(f_globals={}, f_back=None)
        monkeypatch.setattr(structlog._frames.sys, "_getframe", lambda: f1)
        f, n = _find_first_app_frame_and_name()
        assert ((f1, "?") == (f, n))

    def test_tolerates_name_explicitly_None_oneframe(self, monkeypatch):
        """
        Use ``?`` if `f_globals` has a `None` valued `__name__` key
        """
        f1 = stub(f_globals={'__name__': None}, f_back=None)
        monkeypatch.setattr(structlog._frames.sys, "_getframe", lambda: f1)
        f, n = _find_first_app_frame_and_name()
        assert ((f1, "?") == (f, n))

    def test_tolerates_name_explicitly_None_manyframe(self, monkeypatch):
        """
        Use ``?`` if `f_globals` has a `None` valued `__name__` key,
        multiple frames up.
        """
        f1 = stub(f_globals={'__name__': None}, f_back=None)
        f2 = stub(f_globals={'__name__': 'structlog.blubb'}, f_back=f1)
        monkeypatch.setattr(structlog._frames.sys, "_getframe", lambda: f2)
        f, n = _find_first_app_frame_and_name()
        assert ((f1, "?") == (f, n))

    def test_tolerates_f_back_is_None(self, monkeypatch):
        """
        Use ``?`` if all frames are in ignored frames.
        """
        f1 = stub(f_globals={'__name__': 'structlog'}, f_back=None)
        monkeypatch.setattr(structlog._frames.sys, "_getframe", lambda: f1)
        f, n = _find_first_app_frame_and_name()
        assert ((f1, "?") == (f, n))


@pytest.fixture
def exc_info():
    """
    Fake a valid exc_info.
    """
    try:
        raise ValueError
    except ValueError:
        return sys.exc_info()


class TestFormatException(object):
    def test_returns_str(self, exc_info):
        """
        Always returns a native string.
        """
        assert isinstance(_format_exception(exc_info), str)

    def test_formats(self, exc_info):
        """
        The passed exc_info is formatted.
        """
        assert _format_exception(exc_info).startswith(
            "Traceback (most recent call last):\n"
        )

    def test_no_trailing_nl(self, exc_info, monkeypatch):
        """
        Trailing newlines are snipped off but if the string does not contain
        one nothing is removed.
        """
        from structlog._frames import traceback
        monkeypatch.setattr(
            traceback, "print_exception",
            lambda *a: a[-1].write("foo")
        )
        assert "foo" == _format_exception(exc_info)


class TestFormatStack(object):
    def test_returns_str(self):
        """
        Always returns a native string.
        """
        assert isinstance(_format_stack(sys._getframe()), str)

    def test_formats(self):
        """
        The passed stack is formatted.
        """
        assert _format_stack(sys._getframe()).startswith(
            "Stack (most recent call last):\n"
        )

    def test_no_trailing_nl(self, monkeypatch):
        """
        Trailing newlines are snipped off but if the string does not contain
        one nothing is removed.
        """
        from structlog._frames import traceback
        monkeypatch.setattr(
            traceback, "print_stack",
            lambda frame, file: file.write("foo")
        )
        assert _format_stack(sys._getframe()).endswith("foo")
