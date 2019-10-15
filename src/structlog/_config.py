# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Global state department.  Don't reload this module or everything breaks.
"""

from __future__ import absolute_import, division, print_function

import platform
import sys
import warnings

from collections import OrderedDict

from ._generic import BoundLogger
from ._loggers import PrintLoggerFactory
from .dev import ConsoleRenderer, _has_colorama, set_exc_info
from .processors import StackInfoRenderer, TimeStamper, format_exc_info


"""
.. note::

   Any changes to these defaults must be reflected in :doc:`getting-started`.
"""
_BUILTIN_DEFAULT_PROCESSORS = [
    StackInfoRenderer(),
    set_exc_info,
    format_exc_info,
    TimeStamper(fmt="%Y-%m-%d %H:%M.%S", utc=False),
    ConsoleRenderer(colors=_has_colorama),
]
if (
    sys.version_info[:2] >= (3, 6)
    or platform.python_implementation() == "PyPy"
):
    # Python 3.6+ and PyPy have ordered dicts.
    _BUILTIN_DEFAULT_CONTEXT_CLASS = dict
else:
    _BUILTIN_DEFAULT_CONTEXT_CLASS = OrderedDict
_BUILTIN_DEFAULT_WRAPPER_CLASS = BoundLogger
_BUILTIN_DEFAULT_LOGGER_FACTORY = PrintLoggerFactory()
_BUILTIN_CACHE_LOGGER_ON_FIRST_USE = False


class _Configuration(object):
    """
    Global defaults.
    """

    is_configured = False
    default_processors = _BUILTIN_DEFAULT_PROCESSORS[:]
    default_context_class = _BUILTIN_DEFAULT_CONTEXT_CLASS
    default_wrapper_class = _BUILTIN_DEFAULT_WRAPPER_CLASS
    logger_factory = _BUILTIN_DEFAULT_LOGGER_FACTORY
    cache_logger_on_first_use = _BUILTIN_CACHE_LOGGER_ON_FIRST_USE


_CONFIG = _Configuration()
"""
Global defaults used when arguments to :func:`wrap_logger` are omitted.
"""


def is_configured():
    """
    Return whether ``structlog`` has been configured.

    If ``False``, ``structlog`` is running with builtin defaults.

    :rtype: bool

    .. versionadded: 18.1
    """
    return _CONFIG.is_configured


def get_config():
    """
    Get a dictionary with the current configuration.

    .. note::

       Changes to the returned dictionary do *not* affect ``structlog``.

    :rtype: dict

    .. versionadded: 18.1
    """
    return {
        "processors": _CONFIG.default_processors,
        "context_class": _CONFIG.default_context_class,
        "wrapper_class": _CONFIG.default_wrapper_class,
        "logger_factory": _CONFIG.logger_factory,
        "cache_logger_on_first_use": _CONFIG.cache_logger_on_first_use,
    }


def get_logger(*args, **initial_values):
    """
    Convenience function that returns a logger according to configuration.

    >>> from structlog import get_logger
    >>> log = get_logger(y=23)
    >>> log.msg("hello", x=42)
    y=23 x=42 event='hello'

    :param args: *Optional* positional arguments that are passed unmodified to
        the logger factory.  Therefore it depends on the factory what they
        mean.
    :param initial_values: Values that are used to pre-populate your contexts.

    :rtype: A proxy that creates a correctly configured bound logger when
        necessary.

    See :ref:`configuration` for details.

    If you prefer CamelCase, there's an alias for your reading pleasure:
    :func:`structlog.getLogger`.

    .. versionadded:: 0.4.0
        `args`
    """
    return wrap_logger(None, logger_factory_args=args, **initial_values)


getLogger = get_logger
"""
CamelCase alias for :func:`structlog.get_logger`.

This function is supposed to be in every source file -- we don't want it to
stick out like a sore thumb in frameworks like Twisted or Zope.
"""


def wrap_logger(
    logger,
    processors=None,
    wrapper_class=None,
    context_class=None,
    cache_logger_on_first_use=None,
    logger_factory_args=None,
    **initial_values
):
    """
    Create a new bound logger for an arbitrary *logger*.

    Default values for *processors*, *wrapper_class*, and *context_class* can
    be set using :func:`configure`.

    If you set an attribute here, :func:`configure` calls have *no* effect for
    the *respective* attribute.

    In other words: selective overwriting of the defaults while keeping some
    *is* possible.

    :param initial_values: Values that are used to pre-populate your contexts.
    :param tuple logger_factory_args: Values that are passed unmodified as
        ``*logger_factory_args`` to the logger factory if not `None`.

    :rtype: A proxy that creates a correctly configured bound logger when
        necessary.

    See :func:`configure` for the meaning of the rest of the arguments.

    .. versionadded:: 0.4.0
        `logger_factory_args`
    """
    return BoundLoggerLazyProxy(
        logger,
        wrapper_class=wrapper_class,
        processors=processors,
        context_class=context_class,
        cache_logger_on_first_use=cache_logger_on_first_use,
        initial_values=initial_values,
        logger_factory_args=logger_factory_args,
    )


def configure(
    processors=None,
    wrapper_class=None,
    context_class=None,
    logger_factory=None,
    cache_logger_on_first_use=None,
):
    """
    Configures the **global** defaults.

    They are used if :func:`wrap_logger` has been called without arguments.

    Can be called several times, keeping an argument at `None` leaves is
    unchanged from the current setting.

    After calling for the first time, :func:`is_configured` starts returning
    ``True``.

    Use :func:`reset_defaults` to undo your changes.

    :param list processors: List of processors.
    :param type wrapper_class: Class to use for wrapping loggers instead of
        :class:`structlog.BoundLogger`.  See :doc:`standard-library`,
        :doc:`twisted`, and :doc:`custom-wrappers`.
    :param type context_class: Class to be used for internal context keeping.
    :param callable logger_factory: Factory to be called to create a new
        logger that shall be wrapped.
    :param bool cache_logger_on_first_use: `wrap_logger` doesn't return an
        actual wrapped logger but a proxy that assembles one when it's first
        used.  If this option is set to `True`, this assembled logger is
        cached.  See :doc:`performance`.

    .. versionadded:: 0.3.0
        `cache_logger_on_first_use`
    """
    _CONFIG.is_configured = True
    if processors is not None:
        _CONFIG.default_processors = processors
    if wrapper_class is not None:
        _CONFIG.default_wrapper_class = wrapper_class
    if context_class is not None:
        _CONFIG.default_context_class = context_class
    if logger_factory is not None:
        _CONFIG.logger_factory = logger_factory
    if cache_logger_on_first_use is not None:
        _CONFIG.cache_logger_on_first_use = cache_logger_on_first_use


def configure_once(*args, **kw):
    """
    Configures iff structlog isn't configured yet.

    It does *not* matter whether is was configured using :func:`configure`
    or :func:`configure_once` before.

    Raises a :class:`RuntimeWarning` if repeated configuration is attempted.
    """
    if not _CONFIG.is_configured:
        configure(*args, **kw)
    else:
        warnings.warn("Repeated configuration attempted.", RuntimeWarning)


def reset_defaults():
    """
    Resets global default values to builtin defaults.

    :func:`is_configured` starts returning ``False`` afterwards.
    """
    _CONFIG.is_configured = False
    _CONFIG.default_processors = _BUILTIN_DEFAULT_PROCESSORS[:]
    _CONFIG.default_wrapper_class = _BUILTIN_DEFAULT_WRAPPER_CLASS
    _CONFIG.default_context_class = _BUILTIN_DEFAULT_CONTEXT_CLASS
    _CONFIG.logger_factory = _BUILTIN_DEFAULT_LOGGER_FACTORY
    _CONFIG.cache_logger_on_first_use = _BUILTIN_CACHE_LOGGER_ON_FIRST_USE


class BoundLoggerLazyProxy(object):
    """
    Instantiates a BoundLogger on first usage.

    Takes both configuration and instantiation parameters into account.

    The only points where a BoundLogger changes state are bind(), unbind(), and
    new() and that return the actual BoundLogger.

    If and only if configuration says so, that actual BoundLogger is cached on
    first usage.

    .. versionchanged:: 0.4.0
        Added support for `logger_factory_args`.
    """

    def __init__(
        self,
        logger,
        wrapper_class=None,
        processors=None,
        context_class=None,
        cache_logger_on_first_use=None,
        initial_values=None,
        logger_factory_args=None,
    ):
        self._logger = logger
        self._wrapper_class = wrapper_class
        self._processors = processors
        self._context_class = context_class
        self._cache_logger_on_first_use = cache_logger_on_first_use
        self._initial_values = initial_values or {}
        self._logger_factory_args = logger_factory_args or ()

    def __repr__(self):
        return (
            "<BoundLoggerLazyProxy(logger={0._logger!r}, wrapper_class="
            "{0._wrapper_class!r}, processors={0._processors!r}, "
            "context_class={0._context_class!r}, "
            "initial_values={0._initial_values!r}, "
            "logger_factory_args={0._logger_factory_args!r})>".format(self)
        )

    def bind(self, **new_values):
        """
        Assemble a new BoundLogger from arguments and configuration.
        """
        if self._context_class:
            ctx = self._context_class(self._initial_values)
        else:
            ctx = _CONFIG.default_context_class(self._initial_values)
        cls = self._wrapper_class or _CONFIG.default_wrapper_class
        _logger = self._logger
        if not _logger:
            _logger = _CONFIG.logger_factory(*self._logger_factory_args)

        if self._processors is None:
            procs = _CONFIG.default_processors
        else:
            procs = self._processors
        logger = cls(_logger, processors=procs, context=ctx)

        def finalized_bind(**new_values):
            """
            Use cached assembled logger to bind potentially new values.
            """
            if new_values:
                return logger.bind(**new_values)
            else:
                return logger

        if self._cache_logger_on_first_use is True or (
            self._cache_logger_on_first_use is None
            and _CONFIG.cache_logger_on_first_use is True
        ):
            self.bind = finalized_bind
        return finalized_bind(**new_values)

    def unbind(self, *keys):
        """
        Same as bind, except unbind *keys* first.

        In our case that could be only initial values.
        """
        return self.bind().unbind(*keys)

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

    def __getstate__(self):
        """
        Out __getattr__ magic makes this necessary.
        """
        return self.__dict__

    def __setstate__(self, state):
        """
        Out __getattr__ magic makes this necessary.
        """
        for k, v in state.items():
            setattr(self, k, v)
