# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import copy
import pickle
import sys

from io import BytesIO, StringIO

import pytest

from structlog._loggers import (
    WRITE_LOCKS,
    BytesLogger,
    BytesLoggerFactory,
    PrintLogger,
    PrintLoggerFactory,
    WriteLogger,
    WriteLoggerFactory,
)

from .utils import stdlib_log_methods


class TestLoggers:
    """
    Tests common to the Print and WriteLoggers.
    """

    @pytest.fixture(name="logger_cls", params=(WriteLogger, PrintLogger))
    @staticmethod
    def _logger_cls(request):
        return request.param

    def test_prints_to_stdout_by_default(self, logger_cls, capsys):
        """
        Instantiating without arguments gives conveniently a logger to standard
        out.
        """
        logger_cls().msg("hello")

        out, err = capsys.readouterr()
        assert "hello\n" == out
        assert "" == err

    def test_prints_to_correct_file(self, logger_cls, tmpdir, capsys):
        """
        Supplied files are respected.
        """
        f = tmpdir.join("test.log")
        fo = f.open("w")
        logger_cls(fo).msg("hello")
        out, err = capsys.readouterr()

        assert "" == out == err
        fo.close()
        assert "hello\n" == f.read()

    def test_lock(self, logger_cls, sio):
        """
        Creating a logger adds a lock to WRITE_LOCKS.
        """
        assert sio not in WRITE_LOCKS

        logger_cls(sio)

        assert sio in WRITE_LOCKS

    @pytest.mark.parametrize("method", stdlib_log_methods)
    def test_stdlib_methods_support(self, logger_cls, method, sio):
        """
        Print/WriteLogger implements methods of stdlib loggers.
        """
        getattr(logger_cls(sio), method)("hello")

        assert "hello" in sio.getvalue()

    @pytest.mark.parametrize("file", [None, sys.stdout, sys.stderr])
    @pytest.mark.parametrize("proto", range(pickle.HIGHEST_PROTOCOL + 1))
    def test_pickle(self, logger_cls, file, proto):
        """
        Can be pickled and unpickled for stdout and stderr.

        Can't compare output because capsys et all would confuse the logic.
        """
        pl = logger_cls(file=file)

        rv = pickle.loads(pickle.dumps(pl, proto))

        assert pl._file is rv._file
        assert pl._lock is rv._lock

    @pytest.mark.parametrize("proto", range(pickle.HIGHEST_PROTOCOL + 1))
    def test_pickle_not_stdout_stderr(self, logger_cls, tmpdir, proto):
        """
        Loggers with different files than stdout/stderr raise a
        PickingError.
        """
        f = tmpdir.join("file.log")
        f.write("")
        pl = logger_cls(file=f.open())

        with pytest.raises(pickle.PicklingError, match="Only (.+)Loggers to"):
            pickle.dumps(pl, proto)

    def test_deepcopy(self, logger_cls, capsys):
        """
        Deepcopied logger works.
        """
        copied_logger = copy.deepcopy(logger_cls())
        copied_logger.msg("hello")

        out, err = capsys.readouterr()
        assert "hello\n" == out
        assert "" == err

    def test_deepcopy_no_stdout(self, logger_cls, tmp_path):
        """
        Only loggers that log to stdout or stderr can be deepcopy-ed.
        """
        p = tmp_path / "log.txt"
        with p.open(mode="w") as f:
            logger = logger_cls(f)
            logger.msg("hello")

            with pytest.raises(copy.error):
                copy.deepcopy(logger)

        assert "hello\n" == p.read_text()

    def test_repr(self, logger_cls):
        """
        __repr__ makes sense.
        """
        assert repr(logger_cls()).startswith(f"<{logger_cls.__name__}(file=")

    def test_stdout_monkeypatch(self, monkeypatch, capsys):
        """
        If stdout gets monkeypatched, the new instance receives the output.
        """
        p = PrintLogger()
        new_stdout = StringIO()
        monkeypatch.setattr(sys, "stdout", new_stdout)
        p.msg("hello")

        out, err = capsys.readouterr()
        assert "hello\n" == new_stdout.getvalue()
        assert "" == out
        assert "" == err


class TestPrintLoggerFactory:
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


class TestWriteLoggerFactory:
    def test_does_not_cache(self):
        """
        Due to doctest weirdness, we must not re-use WriteLoggers.
        """
        f = WriteLoggerFactory()

        assert f() is not f()

    def test_passes_file(self):
        """
        If a file is passed to the factory, it get passed on to the logger.
        """
        pl = WriteLoggerFactory(sys.stderr)()

        assert sys.stderr is pl._file

    def test_ignores_args(self):
        """
        WriteLogger doesn't take positional arguments.  If any are passed to
        the factory, they are not passed to the logger.
        """
        WriteLoggerFactory()(1, 2, 3)


class TestBytesLogger:
    def test_prints_to_stdout_by_default(self, capsys):
        """
        Instantiating without arguments gives conveniently a logger to standard
        out.
        """
        BytesLogger().msg(b"hell\xc3\xb6")

        out, err = capsys.readouterr()
        assert "hellö\n" == out
        assert "" == err

    def test_prints_to_correct_file(self, tmpdir, capsys):
        """
        Supplied files are respected.
        """
        f = tmpdir.join("test.log")
        fo = f.open("wb")
        BytesLogger(fo).msg(b"hello")
        out, err = capsys.readouterr()

        assert "" == out == err
        fo.close()
        assert "hello\n" == f.read()

    def test_repr(self):
        """
        __repr__ makes sense.
        """
        assert repr(BytesLogger()).startswith("<BytesLogger(file=")

    def test_lock(self, sio):
        """
        Creating a logger adds a lock to WRITE_LOCKS.
        """
        assert sio not in WRITE_LOCKS

        BytesLogger(sio)

        assert sio in WRITE_LOCKS

    @pytest.mark.parametrize("method", stdlib_log_methods)
    def test_stdlib_methods_support(self, method):
        """
        BytesLogger implements methods of stdlib loggers.
        """
        sio = BytesIO()

        getattr(BytesLogger(sio), method)(b"hello")

        assert b"hello" in sio.getvalue()

    @pytest.mark.parametrize(
        "file", [None, sys.stdout.buffer, sys.stderr.buffer]
    )
    @pytest.mark.parametrize("proto", range(pickle.HIGHEST_PROTOCOL + 1))
    def test_pickle(self, file, proto):
        """
        Can be pickled and unpickled for stdout and stderr.

        Can't compare output because capsys et all would confuse the logic.
        """
        pl = BytesLogger(file=file)

        rv = pickle.loads(pickle.dumps(pl, proto))

        assert pl._file is rv._file
        assert pl._lock is rv._lock

    @pytest.mark.parametrize("proto", range(pickle.HIGHEST_PROTOCOL + 1))
    def test_pickle_not_stdout_stderr(self, tmpdir, proto):
        """
        BytesLoggers with different files than stdout/stderr raise a
        PickingError.
        """
        f = tmpdir.join("file.log")
        f.write("")
        pl = BytesLogger(file=f.open())

        with pytest.raises(pickle.PicklingError, match="Only BytesLoggers to"):
            pickle.dumps(pl, proto)

    def test_deepcopy(self, capsys):
        """
        Deepcopied BytesLogger works.
        """
        copied_logger = copy.deepcopy(BytesLogger())
        copied_logger.msg(b"hello")

        out, err = capsys.readouterr()
        assert "hello\n" == out
        assert "" == err

    def test_deepcopy_no_stdout(self, tmp_path):
        """
        Only BytesLoggers that log to stdout or stderr can be deepcopy-ed.
        """
        p = tmp_path / "log.txt"
        with p.open(mode="wb") as f:
            logger = BytesLogger(f)
            logger.msg(b"hello")

            with pytest.raises(copy.error):
                copy.deepcopy(logger)

        assert "hello\n" == p.read_text()


class TestBytesLoggerFactory:
    def test_does_not_cache(self):
        """
        Due to doctest weirdness, we must not re-use BytesLoggers.
        """
        f = BytesLoggerFactory()

        assert f() is not f()

    def test_passes_file(self):
        """
        If a file is passed to the factory, it get passed on to the logger.
        """
        pl = BytesLoggerFactory(sys.stderr)()

        assert sys.stderr is pl._file

    def test_ignores_args(self):
        """
        BytesLogger doesn't take positional arguments.  If any are passed to
        the factory, they are not passed to the logger.
        """
        BytesLoggerFactory()(1, 2, 3)
