# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import absolute_import, division, print_function

import pickle
import sys

import pytest

from six.moves import cStringIO as StringIO

from structlog._loggers import (
    WRITE_LOCKS,
    PrintLogger,
    PrintLoggerFactory,
    ReturnLogger,
    ReturnLoggerFactory,
)
from structlog.stdlib import _NAME_TO_LEVEL


def test_return_logger():
    obj = ["hello"]
    assert obj is ReturnLogger().msg(obj)


STDLIB_MSG_METHODS = [m for m in _NAME_TO_LEVEL if m != "notset"]


class TestPrintLogger(object):
    def test_prints_to_stdout_by_default(self, capsys):
        """
        Instantiating without arguments gives conveniently a logger to standard
        out.
        """
        PrintLogger().msg("hello")

        out, err = capsys.readouterr()
        assert "hello\n" == out
        assert "" == err

    def test_prints_to_correct_file(self, tmpdir, capsys):
        """
        Supplied files are respected.
        """
        f = tmpdir.join("test.log")
        fo = f.open("w")
        PrintLogger(fo).msg("hello")
        out, err = capsys.readouterr()

        assert "" == out == err
        fo.close()
        assert "hello\n" == f.read()

    def test_repr(self):
        """
        __repr__ makes sense.
        """
        assert repr(PrintLogger()).startswith("<PrintLogger(file=")

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

        getattr(PrintLogger(sio), method)("hello")

        assert "hello" in sio.getvalue()

    @pytest.mark.parametrize("file", [None, sys.stdout, sys.stderr])
    @pytest.mark.parametrize("proto", range(pickle.HIGHEST_PROTOCOL))
    def test_pickle(self, file, proto):
        """
        Can be pickled and unpickled for stdout and stderr.

        Can't compare output because capsys et all would confuse the logic.
        """
        pl = PrintLogger(file=file)

        rv = pickle.loads(pickle.dumps(pl, proto))

        assert pl._file is rv._file
        assert pl._lock is rv._lock

    @pytest.mark.parametrize("proto", range(pickle.HIGHEST_PROTOCOL))
    def test_pickle_not_stdout_stderr(self, tmpdir, proto):
        """
        PrintLoggers with differnt files than stdout/stderr raise a
        PickingError.
        """
        f = tmpdir.join("file.log")
        f.write("")
        pl = PrintLogger(file=f.open())

        with pytest.raises(pickle.PicklingError, match="Only PrintLoggers to"):
            pickle.dumps(pl, proto)


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
        pl = PrintLoggerFactory(sys.stderr)()

        assert sys.stderr is pl._file

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
        v = getattr(ReturnLogger(), method)("hello")

        assert "hello" == v


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
