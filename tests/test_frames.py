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
        monkeypatch.undo()
        assert ((f1, 'test') == f, n)

    def test_ignoring_of_additional_frame_names_works(self, monkeypatch):
        """
        Additional names are properly ignored too.
        """
        f1 = stub(f_globals={'__name__': 'test'}, f_back=None)
        f2 = stub(f_globals={'__name__': 'ignored.bar'}, f_back=f1)
        f3 = stub(f_globals={'__name__': 'structlog.blubb'}, f_back=f2)
        monkeypatch.setattr(structlog._frames.sys, '_getframe', lambda: f3)
        f, n = _find_first_app_frame_and_name()
        monkeypatch.undo()
        assert ((f1, 'test') == f, n)


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
        assert isinstance(_format_exception(exc_info), str)

    def test_formats(self, exc_info):
        assert _format_exception(exc_info).startswith(
            'Traceback (most recent call last):\n'
        )


class TestFormatStack(object):
    def test_returns_str(self):
        assert isinstance(_format_stack(sys._getframe()), str)

    def test_formats(self):
        assert _format_stack(sys._getframe()).startswith(
            'Stack (most recent call last):\n'
        )
