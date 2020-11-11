# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Logger wrapper and helper class.
"""

import copy
import sys
import threading

from pickle import PicklingError
from typing import IO, Any, BinaryIO, Dict, Optional, TextIO

from structlog._utils import until_not_interrupted


WRITE_LOCKS: Dict[IO[Any], threading.Lock] = {}


def _get_lock_for_file(file: IO[Any]) -> threading.Lock:
    global WRITE_LOCKS

    lock = WRITE_LOCKS.get(file)
    if lock is None:
        lock = threading.Lock()
        WRITE_LOCKS[file] = lock

    return lock


class PrintLogger:
    """
    Print events into a file.

    :param file: File to print to. (default: `sys.stdout`)

    >>> from structlog import PrintLogger
    >>> PrintLogger().msg("hello")
    hello

    Useful if you follow
    `current logging best practices <logging-best-practices>`.

    Also very useful for testing and examples since logging is finicky in
    doctests.
    """

    def __init__(self, file: Optional[TextIO] = None):
        self._file = file or sys.stdout
        self._write = self._file.write
        self._flush = self._file.flush

        self._lock = _get_lock_for_file(self._file)

    def __getstate__(self) -> str:
        """
        Our __getattr__ magic makes this necessary.
        """
        if self._file is sys.stdout:
            return "stdout"

        elif self._file is sys.stderr:
            return "stderr"

        raise PicklingError(
            "Only PrintLoggers to sys.stdout and sys.stderr can be pickled."
        )

    def __setstate__(self, state: Any) -> None:
        """
        Our __getattr__ magic makes this necessary.
        """
        if state == "stdout":
            self._file = sys.stdout
        else:
            self._file = sys.stderr

        self._write = self._file.write
        self._flush = self._file.flush
        self._lock = _get_lock_for_file(self._file)

    def __deepcopy__(self, memodict: Dict[Any, Any] = {}) -> "PrintLogger":
        """
        Create a new PrintLogger with the same attributes. Similar to pickling.
        """
        if self._file not in (sys.stdout, sys.stderr):
            raise copy.error(
                "Only PrintLoggers to sys.stdout and sys.stderr "
                "can be deepcopied."
            )

        newself = self.__class__(self._file)

        newself._write = newself._file.write
        newself._flush = newself._file.flush
        newself._lock = _get_lock_for_file(newself._file)

        return newself

    def __repr__(self) -> str:
        return f"<PrintLogger(file={self._file!r})>"

    def msg(self, message: str) -> None:
        """
        Print *message*.
        """
        with self._lock:
            until_not_interrupted(self._write, message + "\n")
            until_not_interrupted(self._flush)

    log = debug = info = warn = warning = msg
    fatal = failure = err = error = critical = exception = msg


class PrintLoggerFactory:
    r"""
    Produce `PrintLogger`\ s.

    To be used with `structlog.configure`\ 's ``logger_factory``.

    :param file: File to print to. (default: `sys.stdout`)

    Positional arguments are silently ignored.

    .. versionadded:: 0.4.0
    """

    def __init__(self, file: Optional[TextIO] = None):
        self._file = file

    def __call__(self, *args: Any) -> PrintLogger:
        return PrintLogger(self._file)


class BytesLogger:
    r"""
    Writes bytes into a file.

    :param file: File to print to. (default: `sys.stdout`\ ``.buffer``)

    Useful if you follow
    `current logging best practices <logging-best-practices>` together with
    a formatter that returns bytes (e.g. `orjson
    <https://github.com/ijl/orjson>`_).

    .. versionadded:: 20.2.0
    """
    __slots__ = ("_file", "_write", "_flush", "_lock")

    def __init__(self, file: Optional[BinaryIO] = None):
        self._file = file or sys.stdout.buffer
        self._write = self._file.write
        self._flush = self._file.flush

        self._lock = _get_lock_for_file(self._file)

    def __getstate__(self) -> str:
        """
        Our __getattr__ magic makes this necessary.
        """
        if self._file is sys.stdout.buffer:
            return "stdout"

        elif self._file is sys.stderr.buffer:
            return "stderr"

        raise PicklingError(
            "Only BytesLoggers to sys.stdout and sys.stderr can be pickled."
        )

    def __setstate__(self, state: Any) -> None:
        """
        Our __getattr__ magic makes this necessary.
        """
        if state == "stdout":
            self._file = sys.stdout.buffer
        else:
            self._file = sys.stderr.buffer

        self._write = self._file.write
        self._flush = self._file.flush
        self._lock = _get_lock_for_file(self._file)

    def __deepcopy__(self, memodict: Dict[Any, Any] = {}) -> "BytesLogger":
        """
        Create a new BytesLogger with the same attributes. Similar to pickling.
        """
        if self._file not in (sys.stdout.buffer, sys.stderr.buffer):
            raise copy.error(
                "Only BytesLoggers to sys.stdout and sys.stderr "
                "can be deepcopied."
            )

        newself = self.__class__(self._file)

        newself._write = newself._file.write
        newself._flush = newself._file.flush
        newself._lock = _get_lock_for_file(newself._file)

        return newself

    def __repr__(self) -> str:
        return f"<BytesLogger(file={self._file!r})>"

    def msg(self, message: bytes) -> None:
        """
        Write *message*.
        """
        with self._lock:
            until_not_interrupted(self._write, message + b"\n")
            until_not_interrupted(self._flush)

    log = debug = info = warn = warning = msg
    fatal = failure = err = error = critical = exception = msg


class BytesLoggerFactory:
    r"""
    Produce `BytesLogger`\ s.

    To be used with `structlog.configure`\ 's ``logger_factory``.

    :param file: File to print to. (default: `sys.stdout`\ ``.buffer``)

    Positional arguments are silently ignored.

    .. versionadded:: 20.2.0
    """
    __slots__ = ("_file",)

    def __init__(self, file: Optional[BinaryIO] = None):
        self._file = file

    def __call__(self, *args: Any) -> BytesLogger:
        return BytesLogger(self._file)
