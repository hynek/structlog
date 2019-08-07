# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Logger wrapper and helper class.
"""

from __future__ import absolute_import, division, print_function

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from six import string_types

from structlog.exceptions import DropEvent


if TYPE_CHECKING:
    from structlog._types import EventDict, Processor, ProcessorResult


class BoundLoggerBase(object):
    """
    Immutable context carrier.

    Doesn't do any actual logging; examples for useful subclasses are:

        - the generic :class:`BoundLogger` that can wrap anything,
        - :class:`structlog.twisted.BoundLogger`,
        - and :class:`structlog.stdlib.BoundLogger`.

    See also :doc:`custom-wrappers`.
    """

    _logger = None

    """
    Wrapped logger.

    .. note::

        Despite underscore available **read-only** to custom wrapper classes.

        See also :doc:`custom-wrappers`.
    """

    def __init__(self, logger, processors, context):
        # type: (Any, List[Processor], EventDict) -> None
        self._logger = logger
        self._processors = processors
        self._context = context

    def __repr__(self):
        # type: () -> str
        return "<{0}(context={1!r}, processors={2!r})>".format(
            self.__class__.__name__, self._context, self._processors
        )

    def __eq__(self, other):
        # type: (object) -> bool
        try:
            if self._context == other._context:  # type: ignore
                return True
            else:
                return False
        except AttributeError:
            return False

    def __ne__(self, other):
        # type: (object) -> bool
        return not self.__eq__(other)

    def bind(self, **new_values):
        # type: (**Any) -> BoundLoggerBase
        """
        Return a new logger with *new_values* added to the existing ones.

        :rtype: `self.__class__`
        """
        return self.__class__(
            self._logger,
            self._processors,
            self._context.__class__(self._context, **new_values),
        )

    def unbind(self, *keys):
        # type: (*str) -> BoundLoggerBase
        """
        Return a new logger with *keys* removed from the context.

        :raises KeyError: If the key is not part of the context.

        :rtype: `self.__class__`
        """
        bl = self.bind()
        for key in keys:
            del bl._context[key]
        return bl

    def try_unbind(self, *keys):
        # type: (*str) -> BoundLoggerBase
        """
        Like :meth:`unbind`, but best effort:  missing keys are ignored.

        :rtype: `self.__class__`

        .. versionadded:: 18.2.0
        """
        bl = self.bind()
        for key in keys:
            try:
                del bl._context[key]
            except KeyError:
                pass
        return bl

    def new(self, **new_values):
        # type: (**Any) -> BoundLoggerBase
        """
        Clear context and binds *initial_values* using :func:`bind`.

        Only necessary with dict implementations that keep global state like
        those wrapped by :func:`structlog.threadlocal.wrap_dict` when threads
        are re-used.

        :rtype: `self.__class__`
        """
        self._context.clear()
        return self.bind(**new_values)

    # Helper methods for sub-classing concrete BoundLoggers.

    def _process_event(
        self,
        method_name,  # type: str
        event,  # type: Optional[Any]
        event_kw,  # type: Dict[str, Any]
    ):
        # type: (...) -> ProcessorResult
        """
        Combines creates an `event_dict` and runs the chain.

        Call it to combine your *event* and *context* into an event_dict and
        process using the processor chain.

        :param str method_name: The name of the logger method.  Is passed into
            the processors.
        :param event: The event -- usually the first positional argument to a
            logger.
        :param event_kw: Additional event keywords.  For example if someone
            calls ``log.msg("foo", bar=42)``, *event* would to be ``"foo"``
            and *event_kw* ``{"bar": 42}``.
        :raises: :class:`structlog.DropEvent` if log entry should be dropped.
        :raises: :class:`ValueError` if the final processor doesn't return a
            string, tuple, or a dict.
        :rtype: `tuple` of `(*args, **kw)`

        .. note::

            Despite underscore available to custom wrapper classes.

            See also :doc:`custom-wrappers`.

        .. versionchanged:: 14.0.0
            Allow final processor to return a `dict`.
        """
        event_dict = self._context.copy()
        event_dict.update(**event_kw)
        if event is not None:
            event_dict["event"] = event
        processed_event_dict = event_dict  # type: ProcessorResult
        for proc in self._processors:
            processed_event_dict = proc(
                self._logger, method_name, processed_event_dict
            )
        if isinstance(processed_event_dict, string_types):
            return (processed_event_dict,), {}
        elif isinstance(processed_event_dict, tuple):
            # In this case we assume that the last processor returned a tuple
            # of ``(args, kwargs)`` and pass it right through.
            return processed_event_dict
        elif isinstance(processed_event_dict, dict):
            return (), processed_event_dict
        else:
            raise ValueError(
                "Last processor didn't return an appropriate value.  Allowed "
                "return values are a dict, a tuple of (args, kwargs), or a "
                "string."
            )

    def _proxy_to_logger(self, method_name, event=None, **event_kw):
        # type: (str, Optional[Any], **Any) -> Any
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

            See also :doc:`custom-wrappers`.
        """
        try:
            args, kw = self._process_event(method_name, event, event_kw)
            return getattr(self._logger, method_name)(*args, **kw)
        except DropEvent:
            return
