# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Processors useful regardless of the logging framework.
"""

from __future__ import absolute_import, division, print_function

import calendar
import datetime
import json
import operator
import sys
import time

import six

from structlog._frames import (
    _find_first_app_frame_and_name,
    _format_exception,
    _format_stack,
)


class KeyValueRenderer(object):
    """
    Render `event_dict` as a list of ``Key=repr(Value)`` pairs.

    :param bool sort_keys: Whether to sort keys when formatting.
    :param list key_order: List of keys that should be rendered in this exact
        order.  Missing keys will be rendered as ``None``, extra keys depending
        on *sort_keys* and the dict class.
    :param bool drop_missing: When True, extra keys in *key_order* will be
        dropped rather than rendered as ``None``.

    .. versionadded:: 0.2.0
        *key_order*
    .. versionadded:: 16.1.0
        *drop_missing*
    """
    def __init__(self, sort_keys=False, key_order=None, drop_missing=False):
        # Use an optimized version for each case.
        if key_order and sort_keys:
            def ordered_items(event_dict):
                items = []
                for key in key_order:
                    value = event_dict.pop(key, None)
                    if value is not None or not drop_missing:
                        items.append((key, value))
                items += sorted(event_dict.items())
                return items
        elif key_order:
            def ordered_items(event_dict):
                items = []
                for key in key_order:
                    value = event_dict.pop(key, None)
                    if value is not None or not drop_missing:
                        items.append((key, value))
                items += event_dict.items()
                return items
        elif sort_keys:
            def ordered_items(event_dict):
                return sorted(event_dict.items())
        else:
            ordered_items = operator.methodcaller('items')

        self._ordered_items = ordered_items

    def __call__(self, _, __, event_dict):
        return ' '.join(k + '=' + repr(v)
                        for k, v in self._ordered_items(event_dict))


class UnicodeEncoder(object):
    """
    Encode unicode values in `event_dict`.

    :param str encoding: Encoding to encode to (default: ``'utf-8'``).
    :param str errors: How to cope with encoding errors (default
        ``'backslashreplace'``).

    Useful if you're running Python 2 as otherwise ``u"abc"`` will be rendered
    as ``'u"abc"'``.

    Just put it in the processor chain before the renderer.
    """
    def __init__(self, encoding='utf-8', errors='backslashreplace'):
        self._encoding = encoding
        self._errors = errors

    def __call__(self, logger, name, event_dict):
        for key, value in event_dict.items():
            if isinstance(value, six.text_type):
                event_dict[key] = value.encode(self._encoding, self._errors)
        return event_dict


class UnicodeDecoder(object):
    """
    Decode byte string values in `event_dict`.

    :param str encoding: Encoding to decode from (default: ``'utf-8'``).
    :param str errors: How to cope with encoding errors (default:
        ``'replace'``).

    Useful if you're running Python 3 as otherwise ``b"abc"`` will be rendered
    as ``'b"abc"'``.

    Just put it in the processor chain before the renderer.

    .. versionadded:: 15.4.0
    """
    def __init__(self, encoding='utf-8', errors='replace'):
        self._encoding = encoding
        self._errors = errors

    def __call__(self, logger, name, event_dict):
        for key, value in event_dict.items():
            if isinstance(value, bytes):
                event_dict[key] = value.decode(self._encoding, self._errors)
        return event_dict


class JSONRenderer(object):
    """
    Render the `event_dict` using `json.dumps(event_dict, **json_kw)`.

    :param dict json_kw: Are passed unmodified to `json.dumps()`.
    :param callable serializer: A :meth:`json.dumps`-compatible callable that
        will be used to format the string.  This can be used to use alternative
        JSON encoders like `simplejson
        <https://pypi.python.org/pypi/simplejson/>`_ or `RapidJSON
        <https://pypi.python.org/pypi/python-rapidjson/>`_ (faster but Python
        3-only).

    .. versionadded:: 0.2.0
        Support for ``__structlog__`` serialization method.

    .. versionadded:: 15.4.0
        ``serializer`` parameter.
    """
    def __init__(self, serializer=json.dumps, **dumps_kw):
        self._dumps_kw = dumps_kw
        self._dumps = serializer

    def __call__(self, logger, name, event_dict):
        return self._dumps(event_dict, default=_json_fallback_handler,
                           **self._dumps_kw)


def _json_fallback_handler(obj):
    """
    Serialize custom datatypes and pass the rest to __structlog__ & repr().
    """
    # circular imports :(
    from structlog.threadlocal import _ThreadLocalDictWrapper
    if isinstance(obj, _ThreadLocalDictWrapper):
        return obj._dict
    else:
        try:
            return obj.__structlog__()
        except AttributeError:
            return repr(obj)


def format_exc_info(logger, name, event_dict):
    """
    Replace an `exc_info` field by an `exception` string field:

    If *event_dict* contains the key ``exc_info``, there are two possible
    behaviors:

    - If the value is a tuple, render it into the key ``exception``.
    - If the value is an Exception *and* you're running Python 3, render it
      into the key ``exception``.
    - If the value true but no tuple, obtain exc_info ourselves and render
      that.

    If there is no ``exc_info`` key, the *event_dict* is not touched.
    This behavior is analogue to the one of the stdlib's logging.
    """
    exc_info = event_dict.pop('exc_info', None)
    if exc_info:
        event_dict['exception'] = _format_exception(
            _figure_out_exc_info(exc_info)
        )
    return event_dict


class TimeStamper(object):
    """
    Add a timestamp to `event_dict`.

    .. note::

        You should let OS tools take care of timestamping.  See also
        :doc:`logging-best-practices`.

    :param str format: strftime format string, or ``"iso"`` for `ISO 8601
        <https://en.wikipedia.org/wiki/ISO_8601>`_, or `None` for a `UNIX
        timestamp <https://en.wikipedia.org/wiki/Unix_time>`_.
    :param bool utc: Whether timestamp should be in UTC or local time.
    :param str key: Target key in `event_dict` for added timestamps.
    """
    def __new__(cls, fmt=None, utc=True, key='timestamp'):
        if fmt is None and not utc:
            raise ValueError('UNIX timestamps are always UTC.')

        now_method = getattr(datetime.datetime, 'utcnow' if utc else 'now')
        if fmt is None:
            def stamper(self, _, __, event_dict):
                event_dict[key] = calendar.timegm(time.gmtime())
                return event_dict
        elif fmt.upper() == 'ISO':
            if utc:
                def stamper(self, _, __, event_dict):
                    event_dict[key] = now_method().isoformat() + 'Z'
                    return event_dict
            else:
                def stamper(self, _, __, event_dict):
                    event_dict[key] = now_method().isoformat()
                    return event_dict
        else:
            def stamper(self, _, __, event_dict):
                event_dict[key] = now_method().strftime(fmt)
                return event_dict

        return type('TimeStamper', (object,), {'__call__': stamper})()


def _figure_out_exc_info(v):
    """
    Depending on the Python version will try to do the smartest thing possible
    to transform *v* into an ``exc_info`` tuple.

    :rtype: tuple
    """
    if v is True:
        return sys.exc_info()
    elif six.PY3 and isinstance(v, BaseException):
        return (v.__class__, v, getattr(v, "__traceback__"))

    return v


class ExceptionPrettyPrinter(object):
    """
    Pretty print exceptions and remove them from the `event_dict`.

    :param file file: Target file for output (default: ``sys.stdout``).

    This processor is mostly for development and testing so you can read
    exceptions properly formatted.

    It behaves like :func:`format_exc_info` except it removes the exception
    data from the event dictionary after printing it.

    It's tolerant to having `format_exc_info` in front of itself in the
    processor chain but doesn't require it.  In other words, it handles both
    `exception` as well as `exc_info` keys.

    .. versionadded:: 0.4.0

    .. versionchanged:: 16.0.0
       Added support for passing exceptions as ``exc_info`` on Python 3.
    """
    def __init__(self, file=None):
        if file is not None:
            self._file = file
        else:
            self._file = sys.stdout

    def __call__(self, logger, name, event_dict):
        exc = event_dict.pop("exception", None)
        if exc is None:
            exc_info = _figure_out_exc_info(event_dict.pop("exc_info", None))
            if exc_info:
                exc = _format_exception(exc_info)
        if exc:
            print(exc, file=self._file)
        return event_dict


class StackInfoRenderer(object):
    """
    Add stack information with key `stack` if `stack_info` is true.

    Useful when you want to attach a stack dump to a log entry without
    involving an exception.

    It works analogously to the `stack_info` argument of the Python 3 standard
    library logging but works on both 2 and 3.

    .. versionadded:: 0.4.0
    """
    def __call__(self, logger, name, event_dict):
        if event_dict.pop('stack_info', None):
            event_dict['stack'] = _format_stack(
                _find_first_app_frame_and_name()[0]
            )
        return event_dict
