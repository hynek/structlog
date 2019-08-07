# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Primitives to keep context global but thread (and greenlet) local.
"""

from __future__ import absolute_import, division, print_function

import contextlib
import threading
import uuid

from typing import TYPE_CHECKING, Any, Iterator, Type, Union, cast

from structlog._config import BoundLoggerLazyProxy


if TYPE_CHECKING:
    from structlog._base import BoundLoggerBase
    from structlog._types import EventDict


try:
    from greenlet import getcurrent
except ImportError:
    from threading import local as ThreadLocal
else:
    from weakref import WeakKeyDictionary

    # Mypy has issues with conditional imports
    # https://github.com/python/mypy/issues/1297
    class ThreadLocal(object):  # type: ignore
        """
        threading.local() replacement for greenlets.
        """

        def __init__(self):
            # type: () -> None
            self.__dict__["_weakdict"] = WeakKeyDictionary()

        def __getattr__(self, name):
            # type: (str) -> Any
            key = getcurrent()
            try:
                return self._weakdict[key][name]
            except KeyError:
                raise AttributeError(name)

        def __setattr__(self, name, val):
            # type: (str, str) -> None
            key = getcurrent()
            self._weakdict.setdefault(key, {})[name] = val

        def __delattr__(self, name):
            # type: (str) -> None
            key = getcurrent()
            try:
                del self._weakdict[key][name]
            except KeyError:
                raise AttributeError(name)


def wrap_dict(dict_class):
    # type: (Type) -> Type
    """
    Wrap a dict-like class and return the resulting class.

    The wrapped class and used to keep global in the current thread.

    :param type dict_class: Class used for keeping context.

    :rtype: `type`
    """
    Wrapped = type(
        "WrappedDict-" + str(uuid.uuid4()), (_ThreadLocalDictWrapper,), {}
    )
    setattr(Wrapped, "_tl", ThreadLocal())
    setattr(Wrapped, "_dict_class", dict_class)
    return Wrapped


def as_immutable(logger):
    # type: (Union[BoundLoggerBase, BoundLoggerLazyProxy]) -> BoundLoggerBase
    """
    Extract the context from a thread local logger into an immutable logger.

    :param structlog.BoundLogger logger: A logger with *possibly* thread local
        state.
    :rtype: :class:`~structlog.BoundLogger` with an immutable context.
    """
    if isinstance(logger, BoundLoggerLazyProxy):
        logger = logger.bind()

    try:
        ctx = getattr(logger._context, "_tl").dict_.__class__(
            getattr(logger._context, "_dict")
        )
        bl = logger.__class__(
            logger._logger, processors=logger._processors, context={}
        )
        bl._context = ctx
        return bl
    except AttributeError:
        return logger


@contextlib.contextmanager
def tmp_bind(logger, **tmp_values):
    # type: (BoundLoggerBase, **Any) -> Iterator[BoundLoggerBase]
    """
    Bind *tmp_values* to *logger* & memorize current state. Rewind afterwards.
    """
    saved = as_immutable(logger)._context
    try:
        yield logger.bind(**tmp_values)
    finally:
        logger._context.clear()
        logger._context.update(saved)


class _ThreadLocalDictWrapper(object):
    """
    Wrap a dict-like class and keep the state *global* but *thread-local*.

    Attempts to re-initialize only updates the wrapped dictionary.

    Useful for short-lived threaded applications like requests in web app.

    Use :func:`wrap` to instantiate and use
    :func:`structlog._loggers.BoundLogger.new` to clear the context.
    """

    def __init__(self, *args, **kw):
        # type: (*Any, **Any) -> None
        """
        We cheat.  A context dict gets never recreated.
        """
        if args and isinstance(args[0], self.__class__):
            # our state is global, no need to look at args[0] if it's of our
            # class
            self._dict.update(**kw)
        else:
            self._dict.update(*args, **kw)

    @property
    def _dict(self):  # type: ignore
        """
        Return or create and return the current context.
        """
        try:
            return self.__class__._tl.dict_
        except AttributeError:
            self.__class__._tl.dict_ = self.__class__._dict_class()
            return self.__class__._tl.dict_

    def __repr__(self):
        # type: () -> str
        return "<{0}({1!r})>".format(self.__class__.__name__, self._dict)

    def __eq__(self, other):
        # type: (object) -> bool
        # Same class == same dictionary
        return self.__class__ == other.__class__

    def __ne__(self, other):
        # type: (object) -> bool
        return not self.__eq__(other)

    # Proxy methods necessary for structlog.
    # Dunder methods don't trigger __getattr__ so we need to proxy by hand.
    def __iter__(self):
        # type: () -> Any
        return self._dict.__iter__()

    def __setitem__(self, key, value):
        # type: (Any, Any) -> None
        self._dict[key] = value

    def __delitem__(self, key):
        # type: (Any) -> None
        self._dict.__delitem__(key)

    def __len__(self):
        # type: () -> int
        return cast(int, self._dict.__len__())

    def __getattr__(self, name):
        # type: (Any) -> Any
        method = getattr(self._dict, name)
        return method


_CONTEXT = threading.local()


def merge_threadlocal_context(logger, method_name, event_dict):
    # type: (BoundLoggerBase, str, EventDict) -> Any
    """
    A processor that merges in a global (thread-local) context.

    Use this as your first processor in :func:`structlog.configure` to ensure
    thread-local context is included in all log calls.
    """
    context = _get_context().copy()
    context.update(event_dict)
    return context


def clear_threadlocal():
    # type: () -> None
    """
    Clear the thread-local context.

    The typical use-case for this function is to invoke it early in
    request-handling code.
    """
    _CONTEXT.context = {}


def bind_threadlocal(**kwargs):
    # type: (**Any) -> None
    """
    Put keys and values into the thread-local context.

    Use this instead of :func:`~structlog.BoundLogger.bind` when you want some
    context to be global (thread-local).
    """
    _get_context().update(kwargs)


def _get_context():
    # type: () -> Any
    try:
        return _CONTEXT.context
    except AttributeError:
        _CONTEXT.context = {}
        return _CONTEXT.context
