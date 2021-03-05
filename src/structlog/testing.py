# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Helpers to test your application's logging behavior.

.. versionadded:: 20.1.0

See :doc:`testing`.
"""

from contextlib import contextmanager
from typing import Any, Dict, Generator, List, NamedTuple, NoReturn, Tuple

from ._config import configure, get_config
from .exceptions import DropEvent
from .types import EventDict, WrappedLogger


__all__ = ["LogCapture", "capture_logs"]


class LogCapture:
    """
    Class for capturing log messages in its entries list.
    Generally you should use `structlog.testing.capture_logs`,
    but you can use this class if you want to capture logs with other patterns.

    :ivar List[structlog.types.EventDict] entries: The captured log entries.

    .. versionadded:: 20.1.0
    """

    entries: List[EventDict]

    def __init__(self) -> None:
        self.entries = []

    def __call__(
        self, _: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> NoReturn:
        event_dict["log_level"] = method_name
        self.entries.append(event_dict)

        raise DropEvent


@contextmanager
def capture_logs() -> Generator[List[EventDict], None, None]:
    """
    Context manager that appends all logging statements to its yielded list
    while it is active. Disables all configured processors for the duration
    of the context manager.

    Attention: this is **not** thread-safe!

    .. versionadded:: 20.1.0
    """
    cap = LogCapture()
    old_processors = get_config()["processors"]
    try:
        configure(processors=[cap])
        yield cap.entries
    finally:
        configure(processors=old_processors)


class ReturnLogger:
    """
    Return the arguments that it's called with.

    >>> from structlog import ReturnLogger
    >>> ReturnLogger().msg("hello")
    'hello'
    >>> ReturnLogger().msg("hello", when="again")
    (('hello',), {'when': 'again'})

    .. versionchanged:: 0.3.0
        Allow for arbitrary arguments and keyword arguments to be passed in.
    """

    def msg(self, *args: Any, **kw: Any) -> Any:
        """
        Return tuple of ``args, kw`` or just ``args[0]`` if only one arg passed
        """
        # Slightly convoluted for backwards compatibility.
        if len(args) == 1 and not kw:
            return args[0]
        else:
            return args, kw

    log = debug = info = warn = warning = msg
    fatal = failure = err = error = critical = exception = msg


class ReturnLoggerFactory:
    r"""
    Produce and cache `ReturnLogger`\ s.

    To be used with `structlog.configure`\ 's *logger_factory*.

    Positional arguments are silently ignored.

    .. versionadded:: 0.4.0
    """

    def __init__(self) -> None:
        self._logger = ReturnLogger()

    def __call__(self, *args: Any) -> ReturnLogger:
        return self._logger


class CapturedCall(NamedTuple):
    """
    A call as captured by `CapturingLogger`.

    Can also be unpacked like a tuple.

    :param method_name: The method name that got called.
    :param args: A tuple of the positional arguments.
    :param kwargs: A dict of the keyword arguments.

    .. versionadded:: 20.2.0
    """

    method_name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]


class CapturingLogger:
    """
    Store the method calls that it's been called with.

    This is nicer than `ReturnLogger` for unit tests because the bound logger
    doesn't have to cooperate.

    **Any** method name is supported.

    .. versionadded:: 20.2.0
    """

    calls: List[CapturedCall]

    def __init__(self) -> None:
        self.calls = []

    def __repr__(self) -> str:
        return f"<CapturingLogger with { len(self.calls) } call(s)>"

    def __getattr__(self, name: str) -> Any:
        """
        Capture call to `calls`
        """

        def log(*args: Any, **kw: Any) -> None:
            self.calls.append(CapturedCall(name, args, kw))

        return log


class CapturingLoggerFactory:
    r"""
    Produce and cache `CapturingLogger`\ s.

    Each factory produces and re-uses only **one** logger.

    You can access it via the ``logger`` attribute.

    To be used with `structlog.configure`\ 's *logger_factory*.

    Positional arguments are silently ignored.

    .. versionadded:: 20.2.0
    """
    logger: CapturingLogger

    def __init__(self) -> None:
        self.logger = CapturingLogger()

    def __call__(self, *args: Any) -> CapturingLogger:
        return self.logger
