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

from functools import wraps

from structlog._compat import string_types, OrderedDict
from structlog.common import format_exc_info, KeyValueRenderer


_DEFAULT_PROCESSORS = [format_exc_info, KeyValueRenderer()]
_DEFAULT_DICT_CLASS = OrderedDict


class BoundLogger(object):
    """
    Wraps an arbitrary logger class.

    Allows to bind values to itself and offers a flexible processing pipeline
    for each log entry before relaying the logging call to the wrapped logger.

    Use :func:`wrap` to instantiate, *not* `__init__`.
    """
    _processors = _DEFAULT_PROCESSORS[:]
    _dict_class = _DEFAULT_DICT_CLASS

    def __init__(self, logger, processors, dict_class, event_dict):
        """
        Use :func:`wrap`.
        """
        self._logger = logger
        if processors:
            self._processors = processors
        if dict_class:
            self._dict_class = dict_class
        self._event_dict = event_dict

    @classmethod
    def wrap(cls, logger, processors=None, dict_class=None):
        """
        Create a new `BoundLogger` for an arbitrary `logger`.

        Default values for *processors* and *dict_class* can be set using
        :func:`configure`.

        If you set *processors* here, calls to :func:`configure` have *no*
        effect for the *respective* attribute.

        In other words: selective overwritting of the defaults *is* possible.

        :param logger: An instance of a logger whose method calls will be
            wrapped.
        :param list processors: List of processors.
        :param dict_class: Class to be used for internal dictionary (default:
            `OrderedDict`).

        :rtype: :class:`BoundLogger`
        """
        return cls(
            logger,
            processors,
            dict_class,
            dict_class() if dict_class else cls._dict_class(),
        )

    @classmethod
    def configure(cls, processors=None, dict_class=None):
        """
        Configures the **global** *processors* and *dict_class* that are used
        if :func:`wrap` *has been* or *will be* called without arguments.

        Use :func:`reset_defaults` to undo your changes.

        :param list processors: same as in :func:`wrap`, except `None` means
            "no change".
        """
        if processors:
            cls._processors = processors
        if dict_class:
            cls._dict_class = dict_class

    @classmethod
    def reset_defaults(cls):
        """
        Resets default *processors*.
        """
        cls._processors = _DEFAULT_PROCESSORS[:]
        cls._dict_class = _DEFAULT_DICT_CLASS

    def bind(self, **new_values):
        """
        Memorize all keyword arguments from *new_values* for future log calls.

        :rtype: :class:`BoundLogger`
        """
        event_dict = self._dict_class(self._event_dict, **new_values)
        return self.__class__(
            self._logger, self._processors, self._dict_class, event_dict
        )

    def __getattr__(self, name):
        log_meth = getattr(self._logger, name)

        @wraps(log_meth)
        def wrapped(event=None, **kw):
            """
            Before calling actual logger method, transform the accumulated
            `event_dict` together with the event itself using the processor
            chain.
            """
            res = self._dict_class(self._event_dict, **kw)
            # ensure event to be the last k/v which is useful if an OrderedDict
            # is used.
            if event:
                res.update(event=event)
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
