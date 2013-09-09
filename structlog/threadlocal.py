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
Primitives to keep context global but thread local.
"""

import contextlib
import threading
import uuid

from structlog._config import BoundLoggerLazyProxy


def wrap_dict(dict_class):
    """
    Wrap a dict-like class and return the resulting class.

    The wrapped class and used to keep global in the current thread.

    :param dict_class: Class used for keeping context.

    :rtype: A class.
    """
    Wrapped = type('WrappedDict-' + str(uuid.uuid4()),
                   (_ThreadLocalDictWrapper,), {})
    Wrapped._tl = threading.local()
    Wrapped._dict_class = dict_class
    return Wrapped


def as_immutable(logger):
    """
    Extract the context from a thread local logger into an immutable logger.

    :param BoundLogger logger: A logger with *possibly* thread local state.

    Useful if you want to save and use the context but not modify the global
    state.  For example in class constructors.
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
    Return a temporary logger consisting of *logger*'s context + *tmp_values*.

    Binding new values to *logger* does not affect the contents of the yielded
    logger.

    >>> from structlog import wrap_logger, PrintLogger
    >>> from structlog.threadlocal import tmp_bind, wrap_dict
    >>> logger = wrap_logger(PrintLogger(),  context_class=wrap_dict(dict))
    >>> with tmp_bind(logger, x=5) as tmp_logger:
    ...     logger = logger.bind(y=3)
    ...     tmp_logger.msg('event')
    x=5 event='event'
    >>> logger.msg('event')
    y=3 event='event'
    """
    yield as_immutable(logger).bind(**tmp_values)


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

    def __len__(self):
        return self._dict.__len__()

    def __getattr__(self, name):
        method = getattr(self._dict, name)
        setattr(self, name, method)
        return method
