"""
Type information used throughout ``structlog``.

For now, they are considered provisional. Especially `BindableLogger` will
probably change to something more elegant.

.. versionadded:: 20.2
"""

import sys

from types import TracebackType
from typing import (
    Any,
    Callable,
    Dict,
    Mapping,
    MutableMapping,
    Optional,
    Tuple,
    Type,
    Union,
)


# This construct works better with mypy.
# Doing the obvious ImportError route leads to an 'Incompatible import of
# "Protocol"' error.
if sys.version_info >= (3, 8):
    from typing import Protocol, runtime_checkable
else:
    from typing_extensions import Protocol, runtime_checkable


WrappedLogger = Any
"""
A logger that is wrapped by a bound logger and is ultimately responsible for
the output of the log entries.

``structlog`` makes *no* assumptions about it.

.. versionadded:: 20.2
"""


Context = Union[Dict[str, Any], Dict[Any, Any]]
"""
A dict-like context carrier.

.. versionadded:: 20.2
"""


EventDict = MutableMapping[str, Any]
"""
An event dictionary as it is passed into processors.

It's created by copying the configured `Context` but doesn't need to support
copy itself.

.. versionadded:: 20.2
"""

Processor = Callable[
    [WrappedLogger, str, EventDict],
    Union[Mapping[str, Any], str, Tuple[Any, ...]],
]
"""
A callable that is part of the processor chain.

See :doc:`processors`.

.. versionadded:: 20.2
"""

ExcInfo = Tuple[Type[BaseException], BaseException, Optional[TracebackType]]
"""
An exception info tuple as returned by `sys.exc_info`.

.. versionadded:: 20.2
"""


@runtime_checkable
class BindableLogger(Protocol):
    """
    Methods shared among all bound loggers and that are relied on by
    ``structlog``.


    .. versionadded:: 20.2
    """

    _context: Context

    def bind(self, **new_values: Any) -> "BindableLogger":
        ...

    def unbind(self, *keys: str) -> "BindableLogger":
        ...

    def try_unbind(self, *keys: str) -> "BindableLogger":
        ...

    def new(self, **new_values: Any) -> "BindableLogger":
        ...
