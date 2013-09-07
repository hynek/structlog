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
)
from structlog.processors import (
    KeyValueRenderer,
    format_exc_info,
)

_BUILTIN_DEFAULT_PROCESSORS = [format_exc_info, KeyValueRenderer()]
_BUILTIN_DEFAULT_CONTEXT_CLASS = OrderedDict


class _Configuration(object):
    """
    Global defaults.
    """
    is_configured = False
    default_processors = _BUILTIN_DEFAULT_PROCESSORS[:]
    default_context_class = _BUILTIN_DEFAULT_CONTEXT_CLASS


_CONFIG = _Configuration()
"""
Global defaults used when arguments to :func:`wrap_logger` are omitted.
"""


def wrap_logger(logger, processors=None, context_class=None, **initial_values):
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
    return BoundLoggerLazyProxy(
        logger,
        processors,
        context_class,
        initial_values,
    )


def configure(processors=None, context_class=None):
    """
    Configures the **global** *processors* and *context_class*.

    They are used if :func:`wrap_logger` *has been* or *will be* called without
    arguments.

    Also sets the global class attribute :attr:`is_configured` to `True`.

    Use :func:`reset_defaults` to undo your changes.

    :param list processors: same as in :func:`wrap_logger`, except `None` means
        "no change".
    """
    _CONFIG.is_configured = True
    if processors:
        _CONFIG.default_processors = processors
    if context_class:
        _CONFIG.default_context_class = context_class


def configure_once(processors=None, context_class=None):
    """
    Configures iff structlog isn't configured yet.

    It does *not* matter whether is was configured using :func:`configure`
    or :func:`configure_once` before.

    Raises a RuntimeWarning if repeated configuration is attempted.
    """
    if not _CONFIG.is_configured:
        configure(processors, context_class)
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
    _CONFIG.default_context_class = _BUILTIN_DEFAULT_CONTEXT_CLASS


# def get_logger(processors=None, context_class=None, **initial_values):
#     # TODO!
#     return wrap_logger(_CONFIG.logger_factory(), processors, context_class,
#                 **initial_values)


class BoundLoggerLazyProxy(object):
    """
    Instantiates a BoundLogger on first usage.

    Takes both configuration and instantiation parameters into account.

    The only points where a BoundLogger changes state are bind() and new()
    and that return the actual BoundLogger
    """
    def __init__(self, logger, processors=None, context_class=None,
                 initial_values=None):
        self._logger = logger
        self._processors = processors
        self._context_class = context_class
        self._initial_values = initial_values or {}

    def __repr__(self):
        return (
            '<BoundLoggerLazyProxy(processors={0._processors!r}, '
            'context_class={0._context_class!r}, '
            'initial_values={0._initial_values!r})>'.format(self)
        )

    def bind(self, **new_values):
        if self._context_class:
            ctx = self._context_class(self._initial_values)
        else:
            ctx = _CONFIG.default_context_class(self._initial_values)
        if new_values:
            ctx.update(new_values)
        return BoundLogger(
            self._logger,
            processors=self._processors or _CONFIG.default_processors,
            context=ctx,
        )

    def new(self, **new_values):
        """
        Clear context and binds *initial_values*.

        Only necessary with dict implemenations that keep global state like
        those wrapped by :func:`structlog.threadlocal.wrap_dict` when threads
        are re-used.
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
