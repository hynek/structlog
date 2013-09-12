# Copyright 2013 Hynek Schlawack
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Primitives to keep context global but thread (and greenlet) local.
"""

import contextlib
import uuid

from structlog._config import BoundLoggerLazyProxy

try:
    from greenlet import getcurrent
except ImportError:  # pragma: nocover
    from threading import local as ThreadLocal
else:
    class ThreadLocal(object):  # pragma: nocover
        """
        threading.local() replacement for greenlets.
        """
        def __init__(self):
            self.__dict__["_prefix"] = str(id(self))

        def __getattr__(self, name):
            return getattr(getcurrent(), self._prefix + name)

        def __setattr__(self, name, val):
            setattr(getcurrent(), self._prefix + name, val)

        def __delattr__(self, name):
            delattr(getcurrent(), self._prefix + name)


def wrap_dict(dict_class):
    """
    Wrap a dict-like class and return the resulting class.

    The wrapped class and used to keep global in the current thread.

    :param type dict_class: Class used for keeping context.

    :rtype: `type`
    """
    Wrapped = type('WrappedDict-' + str(uuid.uuid4()),
                   (_ThreadLocalDictWrapper,), {})
    Wrapped._tl = ThreadLocal()
    Wrapped._dict_class = dict_class
    return Wrapped


def as_immutable(logger):
    """
    Extract the context from a thread local logger into an immutable logger.

    :param BoundLogger logger: A logger with *possibly* thread local state.
    :rtype: :class:`~structlog.BoundLogger` with an immutable context.
    """
    if isinstance(logger, BoundLoggerLazyProxy):
        logger = logger.bind()

    try:
        ctx = logger._context._tl.dict_.__class__(logger._context._dict)
        bl = logger.__class__(
            logger._logger,
            processors=logger._processors,
            context={},
        )
        bl._context = ctx
        return bl
    except AttributeError:
        return logger


@contextlib.contextmanager
def tmp_bind(logger, **tmp_values):
    """
    Bind *tmp_values* to *logger* & memorize current state. Rewind afterwards.

    >>> from structlog import wrap_logger, PrintLogger
    >>> from structlog.threadlocal import tmp_bind, wrap_dict
    >>> logger = wrap_logger(PrintLogger(),  context_class=wrap_dict(dict))
    >>> with tmp_bind(logger, x=5) as tmp_logger:
    ...     logger = logger.bind(y=3)
    ...     tmp_logger.msg('event')
    y=3 x=5 event='event'
    >>> logger.msg('event')
    event='event'
    """
    saved = as_immutable(logger)._context
    yield logger.bind(**tmp_values)
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
        return '<{0}({1!r})>'.format(self.__class__.__name__, self._dict)

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
        setattr(self, name, method)
        return method
