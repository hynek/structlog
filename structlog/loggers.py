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
    def __init__(self, logger, processors, event_dict):
        """
        Use :func:`wrap`.
        """
        self._logger = logger
        self._event_dict = event_dict
        if processors:
            self._processors = processors

    @abstractclassmethod
    def wrap(cls, logger, processors=None):
        """
        Wrap *logger*.
        """

    @abstractclassmethod
    def configure(cls, processors):
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
    def bind(self, **new_values):
        """
        Bind values if appropriate.
        """


_DEFAULT_PROCESSORS = [format_exc_info, KeyValueRenderer()]


class BoundLogger(BaseLogger):
    """
    Wraps an arbitrary logger class.

    Allows to bind values to itself and offers a flexible processing pipeline
    for each log entry before relaying the logging call to the wrapped logger.

    Use :func:`wrap` to instantiate, *not* `__init__`.
    """
    _processors = _DEFAULT_PROCESSORS[:]

    @classmethod
    def wrap(cls, logger, processors=None):
        """
        Create a new `BoundLogger` for an arbitrary `logger`.

        Default values for *processors* can be set using :func:`configure`.

        If you set *processors* here, calls to :func:`configure` have *no*
        effect for the *respective* attribute.

        In other words: selective overwritting of the defaults *is* possible.

        :param logger: An instance of a logger whose method calls will be
            wrapped.
        :param list processors: List of processors.

        :rtype: :class:`BoundLogger`
        """
        return cls(
            logger,
            processors,
            {}
        )

    @classmethod
    def configure(cls, processors=None):
        """
        Configures the **global** *processors* that are used if :func:`wrap`
        *has been* or *will be* called without arguments.

        Use :func:`reset_defaults` to undo your changes.

        :param list processors: same as in :func:`wrap`, except `None` means
            "no change".
        """
        if processors:
            cls._processors = processors

    @classmethod
    def reset_defaults(cls):
        """
        Resets default *processors*.
        """
        cls._processors = _DEFAULT_PROCESSORS[:]

    def bind(self, **new_values):
        """
        Memorize all keyword arguments from *new_values* for future log calls.

        :rtype: :class:`BoundLogger`
        """
        event_dict = dict(self._event_dict, **new_values)
        return self.__class__(self._logger, self._processors, event_dict)

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
