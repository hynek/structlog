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
A flexible wrapper for loggers and helper classes.
"""

from __future__ import absolute_import, division, print_function

from abc import ABCMeta, abstractmethod
from functools import wraps

from structlog._compat import string_types, with_metaclass
from structlog.common import format_exc_info, render_kv


class BaseLogger(with_metaclass(ABCMeta)):
    """
    An abstract logger class that allows to bind structured values.

    What happens to those values depends on the concrete implementation.
    """
    @abstractmethod
    def bind(self, **kw):
        """
        Implementation dependent.
        """
        raise NotImplementedError  # pragma: nocover


class BoundLogger(BaseLogger):
    """
    Wraps an arbitrary logger class.

    Allows to bind values to itself and offers a flexible processing pipeline
    for each log entry before relaying the logging call to the wrapped logger.

    Use :func:`fromLogger` to instantiate, *not* `__init__`.
    """
    @classmethod
    def fromLogger(cls, logger, processors=None, bind_filter=None):
        """
        Create a new `BoundLogger` for `logger`.

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
            processors or [
                format_exc_info,
                render_kv,
            ],
            bind_filter,
            {}
        )

    def __init__(self, logger, processors, bind_filter, event_dict):
        """
        Use :func:`fromLogger`.
        """
        self._logger = logger
        self._event_dict = event_dict
        self._processors = processors
        self._bind_filter = bind_filter

    def bind(self, **kw):
        """
        Memorize all keyword arguments from *kw* for future log calls.

        The exact return type depends on the presence of a `bind_filter` and
        its return value:  if `bind_filter` decides that this logger won't be
        logging anymore, a :class:`NOPLogger` is returned.

        Otherwise a new instance of :class:`BoundLogger` is returned.

        :rtype: :class:`BaseLogger`
        """
        if (
            self._bind_filter and
            not self._bind_filter(self._logger, self._event_dict, kw)
        ):
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
                    raise ValueError('Processor returned None.')
                elif res is False:
                    return
            if isinstance(res, string_types):
                args, kw = (res,), {}
            else:
                args, kw = res
            return log_meth(*args, **kw)
        return wrapped


class NOPLogger(BaseLogger):
    """
    A drop-in replacement for `BoundLogger` that does nothing on method calls.

    Useful for returning from an implementation of :func:`BaseLogger.bind()`
    once it's clear that this logger won't be logging.
    """
    def bind(self, _=None, **__):
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
_GLOBAL_NOP_LOGGER = NOPLogger()
