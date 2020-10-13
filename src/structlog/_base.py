# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Logger wrapper and helper class.
"""


from structlog.exceptions import DropEvent


def get_context(bound_logger):
    """
    Return *bound_logger*'s context.

    The type of *bound_logger* and the type returned depend on your
    configuration.

    :param bound_logger: The bound logger whose context you want.

    :returns: The *actual* context from *bound_logger*. It is *not* copied
        first.

    .. versionadded:: 20.2
    """
    # This probably will get more complicated in the future.
    return bound_logger._context


class BoundLoggerBase:
    """
    Immutable context carrier.

    Doesn't do any actual logging; examples for useful subclasses are:

        - the generic :class:`BoundLogger` that can wrap anything,
        - :class:`structlog.twisted.BoundLogger`,
        - and :class:`structlog.stdlib.BoundLogger`.

    See also `custom-wrappers`.
    """

    _logger = None
    """
    Wrapped logger.

    .. note::

        Despite underscore available **read-only** to custom wrapper classes.

        See also `custom-wrappers`.
    """

    def __init__(self, logger, processors, context):
        self._logger = logger
        self._processors = processors
        self._context = context

    def __repr__(self):
        return "<{}(context={!r}, processors={!r})>".format(
            self.__class__.__name__, self._context, self._processors
        )

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

    def bind(self, **new_values):
        """
        Return a new logger with *new_values* added to the existing ones.

        :rtype: ``self.__class__``
        """
        return self.__class__(
            self._logger,
            self._processors,
            self._context.__class__(self._context, **new_values),
        )

    def unbind(self, *keys):
        """
        Return a new logger with *keys* removed from the context.

        :raises KeyError: If the key is not part of the context.

        :rtype: ``self.__class__``
        """
        bl = self.bind()
        for key in keys:
            del bl._context[key]
        return bl

    def try_unbind(self, *keys):
        """
        Like :meth:`unbind`, but best effort: missing keys are ignored.

        :rtype: ``self.__class__``

        .. versionadded:: 18.2.0
        """
        bl = self.bind()
        for key in keys:
            bl._context.pop(key, None)

        return bl

    def new(self, **new_values):
        """
        Clear context and binds *initial_values* using :func:`bind`.

        Only necessary with dict implementations that keep global state like
        those wrapped by `structlog.threadlocal.wrap_dict` when threads
        are re-used.

        :rtype: ``self.__class__``
        """
        self._context.clear()
        return self.bind(**new_values)

    # Helper methods for sub-classing concrete BoundLoggers.

    def _process_event(self, method_name, event, event_kw):
        """
        Combines creates an ``event_dict`` and runs the chain.

        Call it to combine your *event* and *context* into an event_dict and
        process using the processor chain.

        :param str method_name: The name of the logger method.  Is passed into
            the processors.
        :param event: The event -- usually the first positional argument to a
            logger.
        :param event_kw: Additional event keywords.  For example if someone
            calls ``log.msg("foo", bar=42)``, *event* would to be ``"foo"``
            and *event_kw* ``{"bar": 42}``.
        :raises: `structlog.DropEvent` if log entry should be dropped.
        :raises: `ValueError` if the final processor doesn't return a
            string, tuple, or a dict.
        :rtype: `tuple` of ``(*args, **kw)``

        .. note::

            Despite underscore available to custom wrapper classes.

            See also `custom-wrappers`.

        .. versionchanged:: 14.0.0
            Allow final processor to return a `dict`.
        """
        event_dict = self._context.copy()
        event_dict.update(**event_kw)
        if event is not None:
            event_dict["event"] = event
        for proc in self._processors:
            event_dict = proc(self._logger, method_name, event_dict)
        if isinstance(event_dict, str):
            return (event_dict,), {}
        elif isinstance(event_dict, tuple):
            # In this case we assume that the last processor returned a tuple
            # of ``(args, kwargs)`` and pass it right through.
            return event_dict
        elif isinstance(event_dict, dict):
            return (), event_dict
        else:
            raise ValueError(
                "Last processor didn't return an appropriate value.  Allowed "
                "return values are a dict, a tuple of (args, kwargs), or a "
                "string."
            )

    def _proxy_to_logger(self, method_name, event=None, **event_kw):
        """
        Run processor chain on event & call *method_name* on wrapped logger.

        DRY convenience method that runs :func:`_process_event`, takes care of
        handling :exc:`structlog.DropEvent`, and finally calls *method_name* on
        :attr:`_logger` with the result.

        :param str method_name: The name of the method that's going to get
            called.  Technically it should be identical to the method the
            user called because it also get passed into processors.
        :param event: The event -- usually the first positional argument to a
            logger.
        :param event_kw: Additional event keywords.  For example if someone
            calls ``log.msg("foo", bar=42)``, *event* would to be ``"foo"``
            and *event_kw* ``{"bar": 42}``.

        .. note::

            Despite underscore available to custom wrapper classes.

            See also `custom-wrappers`.
        """
        try:
            args, kw = self._process_event(method_name, event, event_kw)
            return getattr(self._logger, method_name)(*args, **kw)
        except DropEvent:
            return


def register_log_level(level_name, level_value):
    # type: (str, str) -> None
    """
    Register and add new custom log level with structlog and Python logging module.
    """
    import logging
    import structlog.stdlib

    level_name_lower = level_name.lower()
    level_name_upper = level_name.upper()

    # Check if the requested log level is already registered with stdlib
    stdlib_log_level_value = getattr(logging, level_name.upper(), None)

    if stdlib_log_level_value is not None:
        raise ValueError("%s log level is already registered with stdlib logging and "
                         "structlog" % (level_name.upper()))

    # Check if the requested log level numeric value is already registed with stdlib
    stdlib_log_level_name = logging.getLevelName(level_value)

    if not stdlib_log_level_value.startswith("Level "):
        raise ValueError("Log level with numeric value %s is already "
                         "registered with stdlib with the following name: %s" %
                         (level_value, stdlib_log_level_name))

    # Register constants with structlog
    setattr(structlog.stdlib, level_value, level_value)
    structlog.stdlib._NAME_TO_LEVEL[level_name_lower] = level_value
    structlog.stdlib._LEVEL_TO_NAME[level_value] = level_name_lower

    # For convenience, add new log.<level name> method
    def make_logger_function(name):
        def log_method(self, msg, *args, **kwargs):
            return self.log(level_value, msg, *args, **kwargs)
        log_method.__name__ = name
        return log_method

    log_method = make_logger_function(level_name_lower)

    setattr(structlog.stdlib._FixedFindCallerLogger, level_name_lower, log_method)
    setattr(structlog.stdlib.BoundLogger, level_name_lower, log_method)

    # Register it with stdlib logging module
    logging.addLevelName(level_value, level_name_upper)
