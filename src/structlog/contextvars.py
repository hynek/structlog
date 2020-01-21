# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Primitives to deal with a concurrency supporting context, as introduced in
Python 3.7 as :mod:`contextvars`.

.. versionadded:: 20.1.0

See :doc:`contextvars`.
"""

from __future__ import absolute_import, division, print_function

import contextvars


_CONTEXT = contextvars.ContextVar("structlog_context")


def merge_contextvars(logger, method_name, event_dict):
    """
    A processor that merges in a global (context-local) context.

    Use this as your first processor in :func:`structlog.configure` to ensure
    context-local context is included in all log calls.

    .. versionadded:: 20.1.0
    """
    ctx = _get_context().copy()
    ctx.update(event_dict)
    return ctx


def clear_contextvars():
    """
    Clear the context-local context.

    The typical use-case for this function is to invoke it early in request-
    handling code.

    .. versionadded:: 20.1.0
    """
    ctx = _get_context()
    ctx.clear()


def bind_contextvars(**kwargs):
    """
    Put keys and values into the context-local context.

    Use this instead of :func:`~structlog.BoundLogger.bind` when you want some
    context to be global (context-local).

    .. versionadded:: 20.1.0
    """
    _get_context().update(kwargs)


def unbind_contextvars(*keys):
    """
    Remove *keys* from the context-local context if they are present.

    Use this instead of :func:`~structlog.BoundLogger.unbind` when you want to
    remove keys from a global (context-local) context.

    .. versionadded:: 20.1.0
    """
    ctx = _get_context()
    for key in keys:
        ctx.pop(key, None)


def _get_context():
    try:
        return _CONTEXT.get()
    except LookupError:
        _CONTEXT.set({})
        return _CONTEXT.get()
