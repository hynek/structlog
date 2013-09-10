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
Global state department.  Don't reload this module or everything breaks.
"""

from __future__ import absolute_import, division, print_function

import warnings

from structlog._compat import OrderedDict
from structlog._loggers import (
    BoundLogger,
    PrintLogger,
)
from structlog.processors import (
    KeyValueRenderer,
    format_exc_info,
)

_BUILTIN_DEFAULT_PROCESSORS = [format_exc_info, KeyValueRenderer()]
_BUILTIN_DEFAULT_CONTEXT_CLASS = OrderedDict
_BUILTIN_DEFAULT_WRAPPER_CLASS = BoundLogger
_BUILTIN_DEFAULT_LOGGER_FACTORY = PrintLogger


class _Configuration(object):
    """
    Global defaults.
    """
    is_configured = False
    default_processors = _BUILTIN_DEFAULT_PROCESSORS[:]
    default_context_class = _BUILTIN_DEFAULT_CONTEXT_CLASS
    default_wrapper_class = _BUILTIN_DEFAULT_WRAPPER_CLASS
    logger_factory = _BUILTIN_DEFAULT_LOGGER_FACTORY


_CONFIG = _Configuration()
"""
Global defaults used when arguments to :func:`wrap_logger` are omitted.
"""


def get_logger(**initial_values):
    """
    Convenience function that returns a logger according to configuration.

    >>> from structlog import get_logger
    >>> log = get_logger(y=23)
    >>> log.msg('hello', x=42)
    y=23 x=42 event='hello'

    :param initial_values: Values that are used to prepopulate your contexts.

    See :ref:`configuration` for details.
    """
    return wrap_logger(None, **initial_values)


def wrap_logger(logger, processors=None, wrapper_class=None,
                context_class=None, **initial_values):
    """
    Create a new bound logger for an arbitrary `logger`.

    Default values for *processors* and *context_class* can be set using
    :func:`configure`.

    If you set *processors* or *context_class* here, calls to
    :func:`configure` have *no* effect for the *respective* attribute.

    In other words: selective overwriting of the defaults *is* possible.

    :param logger: An instance of a logger whose method calls will be
        wrapped.  Use configured logger factory if `None`.
    :param list processors: List of processors.
    :param type wrapper_class: Class to use for wrapping loggers instead of
        :class:`structlog.BoundLogger`.
    :param context_class: Class to be used for internal dictionary.

    :rtype: `cls`
    """
    return BoundLoggerLazyProxy(
        logger,
        wrapper_class=wrapper_class,
        processors=processors,
        context_class=context_class,
        initial_values=initial_values,
    )


def configure(processors=None, wrapper_class=None, context_class=None,
              logger_factory=None):
    """
    Configures the **global** *processors* and *context_class*.

    They are used if :func:`wrap_logger` has been called without arguments.

    Also sets the global class attribute :attr:`is_configured` to `True`.

    Use :func:`reset_defaults` to undo your changes.

    :param list processors: List of processors.
    :param type wrapper_class: Class to use for wrapping loggers instead of
        :class:`structlog.BoundLogger`.
    :param context_class: Class to be used for internal dictionary.
    """
    _CONFIG.is_configured = True
    if processors:
        _CONFIG.default_processors = processors
    if wrapper_class:
        _CONFIG.default_wrapper_class = wrapper_class
    if context_class:
        _CONFIG.default_context_class = context_class
    if logger_factory:
        _CONFIG.logger_factory = logger_factory


def configure_once(*args, **kw):
    """
    Configures iff structlog isn't configured yet.

    It does *not* matter whether is was configured using :func:`configure`
    or :func:`configure_once` before.

    Raises a RuntimeWarning if repeated configuration is attempted.
    """
    if not _CONFIG.is_configured:
        configure(*args, **kw)
    else:
        warnings.warn('Repeated configuration attempted.', RuntimeWarning)


def reset_defaults():
    """
    Resets default *processors*, and *context_class*.

    That means ``[format_exc_info, KeyValueRenderer()]`` for *processors*
    and ``OrderedDict`` for *context_class*.

    Also sets the global class attribute :attr:`is_configured` to `True`.
    """
    _CONFIG.is_configured = False
    _CONFIG.default_processors = _BUILTIN_DEFAULT_PROCESSORS[:]
    _CONFIG.default_wrapper_class = _BUILTIN_DEFAULT_WRAPPER_CLASS
    _CONFIG.default_context_class = _BUILTIN_DEFAULT_CONTEXT_CLASS
    _CONFIG.logger_factory = _BUILTIN_DEFAULT_LOGGER_FACTORY


class BoundLoggerLazyProxy(object):
    """
    Instantiates a BoundLogger on first usage.

    Takes both configuration and instantiation parameters into account.

    The only points where a BoundLogger changes state are bind() and new()
    and that return the actual BoundLogger
    """
    def __init__(self, logger, wrapper_class=None, processors=None,
                 context_class=None, initial_values=None):
        self._logger = logger
        self._wrapper_class = wrapper_class
        self._processors = processors
        self._context_class = context_class
        self._initial_values = initial_values or {}

    def __repr__(self):
        return (
            '<BoundLoggerLazyProxy(logger={0._logger!r}, wrapper_class='
            '{0._wrapper_class!r}, processors={0._processors!r}, '
            'context_class={0._context_class!r}, '
            'initial_values={0._initial_values!r})>'.format(self)
        )

    def bind(self, **new_values):
        """
        Assembles a new BoundLogger from arguments and configuration.
        """
        if self._context_class:
            ctx = self._context_class(self._initial_values)
        else:
            ctx = _CONFIG.default_context_class(self._initial_values)
        if new_values:
            ctx.update(new_values)
        cls = self._wrapper_class or _CONFIG.default_wrapper_class
        if not self._logger:
            self._logger = _CONFIG.logger_factory()
        return cls(
            self._logger,
            processors=self._processors or _CONFIG.default_processors,
            context=ctx,
        )

    def new(self, **new_values):
        """
        Clear context, then bind.
        """
        if self._context_class:
            self._context_class().clear()
        else:
            _CONFIG.default_context_class().clear()
        bl = self.bind(**new_values)
        return bl

    def __getattr__(self, name):
        """
        If a logging method if called on a lazy proxy, we have to create an
        ephemeral BoundLogger first.
        """
        bl = self.bind()
        return getattr(bl, name)
