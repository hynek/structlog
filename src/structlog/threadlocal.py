# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Primitives to keep context global but thread (and greenlet) local.

See `thread-local`.
"""


import contextlib
import threading
import uuid

from structlog._config import BoundLoggerLazyProxy


try:
    from greenlet import getcurrent
except ImportError:
    from threading import local as ThreadLocal
else:
    from weakref import WeakKeyDictionary

    class ThreadLocal:
        """
        threading.local() replacement for greenlets.
        """

        def __init__(self):
            self.__dict__["_weakdict"] = WeakKeyDictionary()

        def __getattr__(self, name):
            key = getcurrent()
            try:
                return self._weakdict[key][name]
            except KeyError:
                raise AttributeError(name)

        def __setattr__(self, name, val):
            key = getcurrent()
            self._weakdict.setdefault(key, {})[name] = val

        def __delattr__(self, name):
            key = getcurrent()
            try:
                del self._weakdict[key][name]
            except KeyError:
                raise AttributeError(name)


def wrap_dict(dict_class):
    """
    Wrap a dict-like class and return the resulting class.

    The wrapped class and used to keep global in the current thread.

    :param type dict_class: Class used for keeping context.

    :rtype: `type`
    """
    Wrapped = type(
        "WrappedDict-" + str(uuid.uuid4()), (_ThreadLocalDictWrapper,), {}
    )
    Wrapped._tl = ThreadLocal()
    Wrapped._dict_class = dict_class
    return Wrapped


def as_immutable(logger):
    """
    Extract the context from a thread local logger into an immutable logger.

    :param structlog.BoundLogger logger: A logger with *possibly* thread local
        state.
    :rtype: :class:`~structlog.BoundLogger` with an immutable context.
    """
    if isinstance(logger, BoundLoggerLazyProxy):
        logger = logger.bind()

    try:
        ctx = logger._context._tl.dict_.__class__(logger._context._dict)
        bl = logger.__class__(
            logger._logger, processors=logger._processors, context={}
        )
        bl._context = ctx
        return bl
    except AttributeError:
        return logger


@contextlib.contextmanager
def tmp_bind(logger, **tmp_values):
    """
    Bind *tmp_values* to *logger* & memorize current state. Rewind afterwards.
    """
    saved = as_immutable(logger)._context
    try:
        yield logger.bind(**tmp_values)
    finally:
        logger._context.clear()
        logger._context.update(saved)


class _ThreadLocalDictWrapper:
    """
    Wrap a dict-like class and keep the state *global* but *thread-local*.

    Attempts to re-initialize only updates the wrapped dictionary.

    Useful for short-lived threaded applications like requests in web app.

    Use :func:`wrap` to instantiate and use
    :func:`structlog._loggers.BoundLogger.new` to clear the context.
    """

    def __init__(self, *args, **kw):
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
    def _dict(self):
        """
        Return or create and return the current context.
        """
        try:
            return self.__class__._tl.dict_
        except AttributeError:
            self.__class__._tl.dict_ = self.__class__._dict_class()
            return self.__class__._tl.dict_

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._dict!r})>"

    def __eq__(self, other):
        # Same class == same dictionary
        return self.__class__ == other.__class__

    def __ne__(self, other):
        return not self.__eq__(other)

    # Proxy methods necessary for structlog.
    # Dunder methods don't trigger __getattr__ so we need to proxy by hand.
    def __iter__(self):
        return self._dict.__iter__()

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __delitem__(self, key):
        self._dict.__delitem__(key)

    def __len__(self):
        return self._dict.__len__()

    def __getattr__(self, name):
        method = getattr(self._dict, name)
        return method


_CONTEXT = threading.local()


def merge_threadlocal(logger, method_name, event_dict):
    """
    A processor that merges in a global (thread-local) context.

    Use this as your first processor in :func:`structlog.configure` to ensure
    thread-local context is included in all log calls.

    .. versionadded:: 19.2.0

    .. versionchanged:: 20.1.0
       This function used to be called ``merge_threalocal_context`` and that
       name is still kept around for backward compatability.
    """
    context = _get_context().copy()
    context.update(event_dict)
    return context


# Alias that shouldn't be used anymore.
merge_threadlocal_context = merge_threadlocal


def clear_threadlocal():
    """
    Clear the thread-local context.

    The typical use-case for this function is to invoke it early in
    request-handling code.

    .. versionadded:: 19.2.0
    """
    _CONTEXT.context = {}


def bind_threadlocal(**kwargs):
    """
    Put keys and values into the thread-local context.

    Use this instead of :func:`~structlog.BoundLogger.bind` when you want some
    context to be global (thread-local).

    .. versionadded:: 19.2.0
    """
    _get_context().update(kwargs)


def unbind_threadlocal(*keys):
    """
    Tries to remove bound *keys* from threadlocal logging context if present.

    .. versionadded:: 20.1.0
    """
    context = _get_context()
    for key in keys:
        context.pop(key, None)


def _get_context():
    try:
        return _CONTEXT.context
    except AttributeError:
        _CONTEXT.context = {}
        return _CONTEXT.context
