# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Primitives to deal with a concurrency supporting context, as introduced in
Python 3.7 as ``contextvars``.
"""

from __future__ import absolute_import, division, print_function

import contextvars


_CONTEXT = contextvars.ContextVar("structlog_context")


def merge_context_local(logger, method_name, event_dict):
    """
    A processor that merges in a global (context-local) context.

    Use this as your first processor in :func:`structlog.configure` to ensure
    context-local context is included in all log calls.
    """
    ctx = _get_context().copy()
    ctx.update(event_dict)
    return ctx


def clear_context_local():
    """
    Clear the context-local context.

    The typical use-case for this function is to invoke it early in request-
    handling code.
    """
    ctx = _get_context()
    ctx.clear()


def bind_context_local(**kwargs):
    """
    Put keys and values into the context-local context.

    Use this instead of :func:`~structlog.BoundLogger.bind` when you want some
    context to be global (context-local).
    """
    _get_context().update(kwargs)


def unbind_context_local(*args):
    """
    Remove keys from the context-local context.

    Use this instead of :func:`~structlog.BoundLogger.unbind` when you want to
    remove keys from a global (context-local) context.
    """
    ctx = _get_context()
    for key in args:
        ctx.pop(key, None)


def _get_context():
    try:
        return _CONTEXT.get()
    except LookupError:
        _CONTEXT.set({})
        return _CONTEXT.get()
