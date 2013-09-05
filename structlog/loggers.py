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
Flexible wrappers for arbitrary loggers.

Allow to bind values to itself and offer a flexible processing pipeline for
each log entry before relaying the logging call to the wrapped logger.

Use class factory method :func:`wrap` to instantiate, *not* the constructor.
"""

from __future__ import absolute_import, division, print_function

from functools import wraps

from structlog._compat import (
    OrderedDict,
    string_types,
)
from structlog.processors import format_exc_info, KeyValueRenderer


_DEFAULT_PROCESSORS = [format_exc_info, KeyValueRenderer()]
_DEFAULT_CONTEXT_CLASS = OrderedDict


class BoundLogger(object):
    """
    *Immutable*, context-carrying wrapper.

    Use class factory method :func:`wrap` to instantiate, *not* the
    constructor.
    """
    _default_processors = _DEFAULT_PROCESSORS[:]
    _default_context_class = _DEFAULT_CONTEXT_CLASS

    is_configured = False
    """
    Global class attribute. Set to `True` once :func:`configure` has run and
    set to `False` again after calling :func:`reset_defaults`.

    Do *not* change by hand.
    """

    def __init__(self, logger, processors, context_class, context):
        self._logger = logger
        self._processors = processors
        self._context_class = context_class
        self._context = context

    def __eq__(self, other):
        try:
            if self._context == other._context:
                return True
            else:
                return False
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def wrap(cls, logger, processors=None, context_class=None):
        """
        Create a new bound logger for an arbitrary `logger`.

        Default values for *processors* and *context_class* can be set using
        :func:`configure`.

        If you set *processors* or *context_class* here, calls to
        :func:`configure` have *no* effect for the *respective* attribute.

        In other words: selective overwritting of the defaults *is* possible.

        :param logger: An instance of a logger whose method calls will be
            wrapped.
        :param list processors: List of processors.
        :param context_class: Class to be used for internal dictionary.

        :rtype: `cls`
        """
        return cls(
            logger,
            processors,
            context_class,
            context_class() if context_class else cls._default_context_class(),
        )

    @classmethod
    def configure(cls, processors=None, context_class=None):
        """
        Configures the **global** *processors* and *context_class*.

        They are used if :func:`wrap` *has been* or *will be* called without
        arguments.

        Also sets the global class attribute :attr:`is_configured` to `True`.

        Use :func:`reset_defaults` to undo your changes.

        :param list processors: same as in :func:`wrap`, except `None` means
            "no change".
        """
        cls.is_configured = True
        if processors:
            cls._default_processors = processors
        if context_class:
            cls._default_context_class = context_class

    @classmethod
    def configure_once(cls, processors=None, context_class=None):
        """
        Calls :func:`configure` iff structlog isn't configured yet.

        It does *not* matter whether is was configured using :func:`configure`
        or :func:`configure_once` before.
        """
        if not cls.is_configured:
            cls.configure(processors=processors, context_class=context_class)

    @classmethod
    def reset_defaults(cls):
        """
        Resets default *processors*, and *context_class*.

        That means ``[format_exc_info, KeyValueRenderer()]`` for *processors*
        and ``OrderedDict`` for *context_class*.

        Also sets the global class attribute :attr:`is_configured` to `True`.
        """
        cls.is_configured = False
        cls._default_processors = _DEFAULT_PROCESSORS[:]
        cls._default_context_class = _DEFAULT_CONTEXT_CLASS

    @property
    def _current_processors(self):
        if self._processors is not None:
            return self._processors
        else:
            return self.__class__._default_processors

    @property
    def _current_context_class(self):
        if self._context_class is not None:
            return self._context_class
        else:
            return self.__class__._default_context_class

    def __getattr__(self, name):
        """
        If not done yet, wrap the desired logger method & cache the result.
        """
        log_meth = getattr(self._logger, name)

        @wraps(log_meth)
        def wrapped(event=None, **kw):
            """
            Before calling actual logger method, transform the accumulated
            `context` together with the event itself using the processor
            chain.
            """
            if self._context.__class__ != self._current_context_class:
                # happens if a wrapped logger is called w/o binding anything.
                # E.g. a different module calls directly log.info('event').
                self._context = self._current_context_class(self._context)
            # copy() makes sure that dicts like those from
            # _ThreadLocalDictWrapper don't get mangled.
            event_dict = self._context.copy()
            event_dict.update(**kw)
            if event:
                event_dict.update(event=event)
            for processor in self._current_processors:
                event_dict = processor(self._logger, name, event_dict)
                if event_dict is None:
                    raise ValueError('Processor {0!r} returned None.'
                                     .format(processor))
                elif event_dict is False:
                    return
            if isinstance(event_dict, string_types):
                args, kw = (event_dict,), {}
            else:
                args, kw = event_dict
            return log_meth(*args, **kw)
        setattr(self, name, wrapped)
        return wrapped

    def bind(self, **new_values):
        """
        Return a new logger with *new_values* added to the existing ones.

        :rtype: :class:`BoundLogger`
        """
        return self.__class__(
            self._logger,
            self._processors,
            self._context_class,
            self._current_context_class(self._context, **new_values)
        )

    def new(self, **initial_values):
        """
        Clear context and binds *initial_values*.

        Only necessary with dict implemenations that keep global state like
        those wrapped by :func:`structlog.threadlocal.wrap_dict` when threads
        are re-used.
        """
        self._context.clear()
        return self.bind(**initial_values)

    def __repr__(self):
        return '<BoundLogger(context={0!r}, processors={1!r})>'.format(
            self._context,
            self._current_processors,
        )
