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
A flexible wrapper for loggers and its helper classes.
"""

from __future__ import absolute_import, division, print_function

from abc import ABCMeta, abstractmethod
from functools import wraps

from structlog._compat import string_types, with_metaclass, abstractclassmethod
from structlog.common import format_exc_info, KeyValueRenderer


class BaseLogger(with_metaclass(ABCMeta)):
    """
    An abstract logger class that allows to bind structured values.

    What happens to those values depends on the concrete implementation.
    """
    def __init__(self, logger, processors, bind_filter, event_dict):
        """
        Use :func:`wrap`.
        """
        self._logger = logger
        self._event_dict = event_dict
        if processors:
            self._processors = processors
        if bind_filter:
            self._bind_filter = bind_filter

    @abstractclassmethod
    def wrap(cls, logger, processors=None, bind_filter=None):
        """
        Wrap *logger*.
        """

    @abstractclassmethod
    def configure(cls, processors, bind_filter):
        """
        Configure *default* values for *all* loggers.
        """

    @abstractclassmethod
    def reset_defaults(cls):
        """
        Reset global default values to original values.

        Useful for cleanup functions while testing.
        """

    @abstractmethod
    def bind(self, **kw):
        """
        Bind values if appropriate.
        """


def _always_true(*_, **__):
    """
    Return `True` no matter what.
    """
    return True


_DEFAULT_PROCESSORS = [format_exc_info, KeyValueRenderer()]
_DEFAULT_BIND_FILTER = _always_true


class BoundLogger(BaseLogger):
    """
    Wraps an arbitrary logger class.

    Allows to bind values to itself and offers a flexible processing pipeline
    for each log entry before relaying the logging call to the wrapped logger.

    Use :func:`wrap` to instantiate, *not* `__init__`.
    """
    _processors = _DEFAULT_PROCESSORS[:]
    # save as array so it can be modified globally
    _bind_filter = [_DEFAULT_BIND_FILTER]

    @classmethod
    def wrap(cls, logger, processors=None, bind_filter=None):
        """
        Create a new `BoundLogger` for an arbitrary `logger`.

        Default values for *processors* and *bind_filter* can be set using
        :func:`configure`.

        If you set *processors* or *bind_filter* here, calls to
        :func:`configure` have *no* effect for the *respective* attribute.

        In other words: selective overwritting of the defaults *is* possible.

        :param logger: An instance of a logger whose method calls will be
            wrapped.
        :param list processors: List of processors.
        :param callable bind_filter: Gets called as
            ``bind_filter(logger, current_event_dict, keywords_to_add)`` on
            each call to :func:`bind`.  Once it returns ``False``, `bind()`
            returns a stub that ignores all calls.

        :rtype: :class:`BoundLogger`
        """
        return cls(
            logger,
            processors,
            [bind_filter] if bind_filter else None,
            {}
        )

    @classmethod
    def configure(cls, processors=None, bind_filter=None):
        """
        Use configure the *global* default settings that are used if
        :func:`wrap` *has been* or *will be* called without arguments.

        Use :func:`reset_defaults` to undo your changes.

        :param list processors: same as in :func:`wrap`, except `None` means
            "no change".
        :param callable bind_filters: same as in :func:`wrap`, except `None`
            means "no change".
        """
        if processors:
            del cls._processors[:]
            cls._processors.extend(processors)
        if bind_filter:
            cls._bind_filter[0] = bind_filter

    @classmethod
    def reset_defaults(cls):
        """
        Resets default *processors* and *bind_filter*.
        """
        del cls._processors[:]
        cls._processors.extend(_DEFAULT_PROCESSORS)
        cls._bind_filter[0] = _DEFAULT_BIND_FILTER

    def bind(self, **kw):
        """
        Memorize all keyword arguments from *kw* for future log calls.

        The exact return type depends on the presence of a `bind_filter` and
        its return value:  if `bind_filter` decides that this logger won't be
        logging anymore, a :class:`NOPLogger` is returned.

        Otherwise a new instance of :class:`BoundLogger` is returned.

        :rtype: :class:`BaseLogger`
        """
        if not self._bind_filter[0](self._logger, self._event_dict, kw):
            return _GLOBAL_NOP_LOGGER
        event_dict = dict(self._event_dict, **kw)
        return self.__class__(self._logger, self._processors,
                              self._bind_filter, event_dict)

    def __getattr__(self, name):
        log_meth = getattr(self._logger, name)

        @wraps(log_meth)
        def wrapped(event=None, **kw):
            """
            Before calling actual logger method, transform the accumulated
            `event_dict` together with the event itself using the processor
            chain.
            """
            res = dict(self._event_dict, event=event, **kw)
            for processor in self._processors:
                res = processor(self._logger, name, res)
                if res is None:
                    raise ValueError('Processor {0!r} returned None.'
                                     .format(processor))
                elif res is False:
                    return
            if isinstance(res, string_types):
                args, kw = (res,), {}
            else:
                args, kw = res
            return log_meth(*args, **kw)
        setattr(self, name, wrapped)
        return wrapped


class NOPLogger(BaseLogger):
    """
    A drop-in replacement for `BoundLogger` that does nothing on method calls.

    Useful for returning from an implementation of :func:`BaseLogger.bind()`
    once it's clear that this logger won't be logging.
    """
    @classmethod
    def wrap(cls, logger, processors=None, bind_filter=None):
        """
        Return global instance of :class:`NOPLogger`.

        :rtype: :class:`NOPLogger`
        """
        return _GLOBAL_NOP_LOGGER

    @classmethod
    def configure(self, *_, **__):
        """
        Do absolutely nothing.
        """

    @classmethod
    def reset_defaults(self, *_, **__):
        """
        Do absolutely nothing.
        """

    def bind(self, **__):
        """
        Return ourselves.

        :rtype: :class:`NOPLogger`
        """
        return self

    def _nop(*_, **__):
        """
        Do absolutely nothing.
        """

    def __getattr__(self, _):
        return self._nop


# `NOPLogger` is immutable and stateless so there's no point of having more
# than one around.
_GLOBAL_NOP_LOGGER = NOPLogger(None, None, None, None)
