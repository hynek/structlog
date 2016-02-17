# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import absolute_import, division, print_function

import sys

import pytest

from six.moves import cStringIO as StringIO
from structlog._loggers import (
    PrintLogger,
    PrintLoggerFactory,
    ReturnLogger,
    ReturnLoggerFactory,
    WRITE_LOCKS,
)
from structlog.stdlib import _NAME_TO_LEVEL


def test_return_logger():
    obj = ['hello']
    assert obj is ReturnLogger().msg(obj)


STDLIB_MSG_METHODS = [m for m in _NAME_TO_LEVEL if m != 'notset']


class TestPrintLogger(object):
    def test_prints_to_stdout_by_default(self, capsys):
        """
        Instantiating without arguments gives conveniently a logger to standard
        out.
        """
        PrintLogger().msg('hello')
        out, err = capsys.readouterr()
        assert 'hello\n' == out
        assert '' == err

    def test_prints_to_correct_file(self, tmpdir, capsys):
        """
        Supplied files are respected.
        """
        f = tmpdir.join('test.log')
        fo = f.open('w')
        PrintLogger(fo).msg('hello')
        out, err = capsys.readouterr()
        assert '' == out == err
        fo.close()
        assert 'hello\n' == f.read()

    def test_repr(self):
        """
        __repr__ makes sense.
        """
        assert repr(PrintLogger()).startswith(
            "<PrintLogger(file="
        )

    def test_lock(self):
        """
        Creating a logger adds a lock to WRITE_LOCKS.
        """
        sio = StringIO()
        assert sio not in WRITE_LOCKS
        PrintLogger(sio)
        assert sio in WRITE_LOCKS

    @pytest.mark.parametrize("method", STDLIB_MSG_METHODS)
    def test_stdlib_methods_support(self, method):
        """
        PrintLogger implements methods of stdlib loggers.
        """
        sio = StringIO()
        getattr(PrintLogger(sio), method)('hello')
        assert 'hello' in sio.getvalue()


class TestPrintLoggerFactory(object):
    def test_does_not_cache(self):
        """
        Due to doctest weirdness, we must not re-use PrintLoggers.
        """
        f = PrintLoggerFactory()
        assert f() is not f()

    def test_passes_file(self):
        """
        If a file is passed to the factory, it get passed on to the logger.
        """
        l = PrintLoggerFactory(sys.stderr)()
        assert sys.stderr is l._file

    def test_ignores_args(self):
        """
        PrintLogger doesn't take positional arguments.  If any are passed to
        the factory, they are not passed to the logger.
        """
        PrintLoggerFactory()(1, 2, 3)


class ReturnLoggerTest(object):
    @pytest.mark.parametrize("method", STDLIB_MSG_METHODS)
    def test_stdlib_methods_support(self, method):
        """
        ReturnLogger implements methods of stdlib loggers.
        """
        v = getattr(ReturnLogger(), method)('hello')
        assert 'hello' == v


class TestReturnLoggerFactory(object):
    def test_builds_returnloggers(self):
        f = ReturnLoggerFactory()
        assert isinstance(f(), ReturnLogger)

    def test_caches(self):
        """
        There's no need to have several loggers so we return the same one on
        each call.
        """
        f = ReturnLoggerFactory()
        assert f() is f()

    def test_ignores_args(self):
        """
        ReturnLogger doesn't take positional arguments.  If any are passed to
        the factory, they are not passed to the logger.
        """
        ReturnLoggerFactory()(1, 2, 3)
