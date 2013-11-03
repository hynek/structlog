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
Processors useful regardless of the logging framework.
"""

from __future__ import absolute_import, division, print_function

import calendar
import datetime
import json
import operator
import sys
import time
import traceback

from structlog._compat import StringIO, unicode_type


class KeyValueRenderer(object):
    """
    Render `event_dict` as a list of ``Key=repr(Value)`` pairs.

    :param bool sort_keys: Whether to sort keys when formatting.
    :param list key_order: List of keys that should be rendered in this exact
        order.  Missing keys will be rendered as `None`, extra keys depending
        on *sort_keys* and the dict class.

        .. versionadded:: 0.2.0

    >>> from structlog.processors import KeyValueRenderer
    >>> KeyValueRenderer(sort_keys=True)(None, None, {'a': 42, 'b': [1, 2, 3]})
    'a=42 b=[1, 2, 3]'
    >>> KeyValueRenderer(key_order=['b', 'a'])(None, None,
    ...                                       {'a': 42, 'b': [1, 2, 3]})
    'b=[1, 2, 3] a=42'
    """
    def __init__(self, sort_keys=False, key_order=None):
        # Use an optimized version for each case.
        if key_order and sort_keys:
            def ordered_items(event_dict):
                items = []
                for key in key_order:
                    value = event_dict.pop(key, None)
                    items.append((key, value))
                items += sorted(event_dict.items())
                return items
        elif key_order:
            def ordered_items(event_dict):
                items = []
                for key in key_order:
                    value = event_dict.pop(key, None)
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

    :param str encoding: Encoding to encode to (default: ``'utf-8'``.
    :param str errors: How to cope with encoding errors (default
        ``'backslashreplace'``).

    Useful for :class:`KeyValueRenderer` if you don't want to see u-prefixes:

    >>> from structlog.processors import KeyValueRenderer, UnicodeEncoder
    >>> KeyValueRenderer()(None, None, {'foo': u'bar'})
    "foo=u'bar'"
    >>> KeyValueRenderer()(None, None,
    ...                    UnicodeEncoder()(None, None, {'foo': u'bar'}))
    "foo='bar'"

    or :class:`JSONRenderer` and :class:`structlog.twisted.JSONRenderer` to
    make sure user-supplied strings don't break the renderer.

    Just put it in the processor chain before the renderer.
    """
    def __init__(self, encoding='utf-8', errors='backslashreplace'):
        self._encoding = encoding
        self._errors = errors

    def __call__(self, logger, name, event_dict):
        for key, value in event_dict.items():
            if isinstance(value, unicode_type):
                event_dict[key] = value.encode(self._encoding, self._errors)
        return event_dict


class JSONRenderer(object):
    """
    Render the `event_dict` using `json.dumps(event_dict, **json_kw)`.

    :param json_kw: Are passed unmodified to `json.dumps()`.

    >>> from structlog.processors import JSONRenderer
    >>> JSONRenderer(sort_keys=True)(None, None, {'a': 42, 'b': [1, 2, 3]})
    '{"a": 42, "b": [1, 2, 3]}'

    Bound objects are attempted to be serialize using a ``__structlog__`
    method.  If none is defined, ``repr()`` is used:

    >>> class C1(object):
    ...     def __structlog__(self):
    ...         return ['C1!']
    ...     def __repr__(self):
    ...         return '__structlog__ took precedence'
    >>> class C2(object):
    ...     def __repr__(self):
    ...         return 'No __structlog__, so this is used.'
    >>> from structlog.processors import JSONRenderer
    >>> JSONRenderer(sort_keys=True)(None, None, {'c1': C1(), 'c2': C2()})
    '{"c1": ["C1!"], "c2": "No __structlog__, so this is used."}'

    Please note that additionally to strings, you can also return any type
    the standard library JSON module knows about -- like in this example
    a list.

    .. versionchanged:: 0.2.0
        Added support for ``__structlog__`` serialization method.
    """
    def __init__(self, **dumps_kw):
        self._dumps_kw = dumps_kw

    def __call__(self, logger, name, event_dict):
        return json.dumps(event_dict, cls=_JSONFallbackEncoder,
                          **self._dumps_kw)


class _JSONFallbackEncoder(json.JSONEncoder):
    """
    Serialize custom datatypes and pass the rest to __structlog__ & repr().
    """
    def default(self, obj):
        """
        Serialize obj with repr(obj) as fallback.
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
    - If the value true but no tuple, obtain exc_info ourselves and render
      that.

    If there is no ``exc_info`` key, the *event_dict* is not touched.
    This behavior is analogue to the one of the stdlib's logging.

    >>> from structlog.processors import format_exc_info
    >>> try:
    ...     raise ValueError
    ... except ValueError:
    ...     format_exc_info(None, None, {'exc_info': True})# doctest: +ELLIPSIS
    {'exception': 'Traceback (most recent call last):...
    """
    exc_info = event_dict.pop('exc_info', None)
    if exc_info:
        if not isinstance(exc_info, tuple):
            exc_info = sys.exc_info()
        event_dict['exception'] = _format_exception(exc_info)
    return event_dict


def _format_exception(exc_info):
    """
    Prettyprint an `exc_info` tuple.

    Shamelessly stolen from stdlib's logging module.
    """
    sio = StringIO()
    traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], None, sio)
    s = sio.getvalue()
    sio.close()
    if s[-1:] == "\n":
        s = s[:-1]
    return s


class TimeStamper(object):
    """
    Add a timestamp to `event_dict`.

    :param str format: strftime format string, or ``"iso"`` for `ISO 8601
        <http://en.wikipedia.org/wiki/ISO_8601>`_, or `None` for a `UNIX
        timestamp <http://en.wikipedia.org/wiki/Unix_time>`_.
    :param bool utc: Whether timestamp should be in UTC or local time.

    >>> from structlog.processors import TimeStamper
    >>> TimeStamper()(None, None, {})  # doctest: +SKIP
    {'timestamp': 1378994017}
    >>> TimeStamper(fmt='iso')(None, None, {})  # doctest: +SKIP
    {'timestamp': '2013-09-12T13:54:26.996778Z'}
    >>> TimeStamper(fmt='%Y')(None, None, {})  # doctest: +SKIP
    {'timestamp': '2013'}
    """
    def __new__(cls, fmt=None, utc=True):
        if fmt is None and not utc:
            raise ValueError('UNIX timestamps are always UTC.')

        now_method = getattr(datetime.datetime, 'utcnow' if utc else 'now')
        if fmt is None:
            def stamper(self, _, __, event_dict):
                event_dict['timestamp'] = calendar.timegm(time.gmtime())
                return event_dict
        elif fmt.upper() == 'ISO':
            if utc:
                def stamper(self, _, __, event_dict):
                    event_dict['timestamp'] = now_method().isoformat() + 'Z'
                    return event_dict
            else:
                def stamper(self, _, __, event_dict):
                    event_dict['timestamp'] = now_method().isoformat()
                    return event_dict
        else:
            def stamper(self, _, __, event_dict):
                event_dict['timestamp'] = now_method().strftime(fmt)
                return event_dict

        return type('TimeStamper', (object,), {'__call__': stamper})()


class ExceptionPrettyPrinter(object):
    """
    Pretty print exceptions and remove them from the `event_dict`.

    :param file file: Target file for output (default: `sys.stdout`).

    This processor is mostly for development and testing so you can read
    exceptions properly formatted.

    It behaves like :func:`format_exc_info` except it removes the exception
    data from the event dictionary after printing it.

    It's tolerant to having `format_exc_info` in front of itself in the
    processor chain but doesn't require it.  In other words, it handles both
    `exception` as well as `exc_info` keys.
    """
    def __init__(self, file=None):
        if file is not None:
            self._file = file
        else:
            self._file = sys.stdout

    def __call__(self, logger, name, event_dict):
        exc = event_dict.pop('exception', None)
        if exc is None:
            exc_info = event_dict.pop('exc_info', None)
            if exc_info:
                if not isinstance(exc_info, tuple):
                    exc_info = sys.exc_info()
                exc = _format_exception(exc_info)
        if exc:
            print(exc, file=self._file)
        return event_dict
