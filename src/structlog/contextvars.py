# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Primitives to deal with a concurrency supporting context, as introduced in
Python 3.7 as :mod:`contextvars`.

.. versionadded:: 20.1.0
.. versionchanged:: 21.1.0
   Reimplemented without using a single dict as context carrier for improved
   isolation. Every key-value pair is a separate `contextvars.ContextVar` now.

See :doc:`contextvars`.
"""

import contextvars

from typing import Any, Dict

from .types import EventDict, WrappedLogger


STRUCTLOG_KEY_PREFIX = "structlog_"
_CONTEXT_VARS: Dict[str, contextvars.ContextVar[Any]] = {}


def merge_contextvars(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    A processor that merges in a global (context-local) context.

    Use this as your first processor in :func:`structlog.configure` to ensure
    context-local context is included in all log calls.

    .. versionadded:: 20.1.0
    .. versionchanged:: 21.1.0 See toplevel note.
    """
    ctx = contextvars.copy_context()

    for k in ctx:
        if k.name.startswith(STRUCTLOG_KEY_PREFIX) and ctx[k] is not Ellipsis:
            event_dict.setdefault(k.name[len(STRUCTLOG_KEY_PREFIX) :], ctx[k])

    return event_dict


def clear_contextvars() -> None:
    """
    Clear the context-local context.

    The typical use-case for this function is to invoke it early in request-
    handling code.

    .. versionadded:: 20.1.0
    .. versionchanged:: 21.1.0 See toplevel note.
    """
    ctx = contextvars.copy_context()
    for k in ctx:
        if k.name.startswith(STRUCTLOG_KEY_PREFIX):
            k.set(Ellipsis)


def bind_contextvars(**kw: Any) -> None:
    """
    Put keys and values into the context-local context.

    Use this instead of :func:`~structlog.BoundLogger.bind` when you want some
    context to be global (context-local).

    .. versionadded:: 20.1.0
    .. versionchanged:: 21.1.0 See toplevel note.
    """
    for k, v in kw.items():
        structlog_k = f"{STRUCTLOG_KEY_PREFIX}{k}"
        try:
            var = _CONTEXT_VARS[structlog_k]
        except KeyError:
            var = contextvars.ContextVar(structlog_k, default=Ellipsis)
            _CONTEXT_VARS[structlog_k] = var

        var.set(v)


def unbind_contextvars(*keys: str) -> None:
    """
    Remove *keys* from the context-local context if they are present.

    Use this instead of :func:`~structlog.BoundLogger.unbind` when you want to
    remove keys from a global (context-local) context.

    .. versionadded:: 20.1.0
    .. versionchanged:: 21.1.0 See toplevel note.
    """
    for k in keys:
        structlog_k = f"{STRUCTLOG_KEY_PREFIX}{k}"
        if structlog_k in _CONTEXT_VARS:
            _CONTEXT_VARS[structlog_k].set(Ellipsis)
