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

import json
import sys
import traceback

from functools import partial
from operator import attrgetter

from structlog._compat import StringIO, unicode_type
from structlog.threadlocal import ThreadLocalDict


class KeyValueRenderer(object):
    """
    Render `event_dict` as a list of ``Key=repr(Value)`` pairs.

    :param bool sort_keys: Whether to sort keys when formatting.
    """
    def __init__(self, sort_keys=False):
        self._sort_keys = sort_keys

    def __call__(self, _, __, event_dict):
        if self._sort_keys:
            items = sorted(event_dict.items())
        else:
            items = event_dict.items()

        return ' '.join(k + '=' + repr(v) for k, v in items)


class UnicodeEncoder(object):
    """
    Encode unicode values in `event_dict`.

    Useful for KeyValueRenderer if you don't want to see u-prefixes.
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
    """
    def __init__(self, **dumps_kw):
        self._dumps_kw = dumps_kw

    def __call__(self, logger, name, event_dict):
        return json.dumps(event_dict, cls=_JSONFallbackEncoder,
                          **self._dumps_kw)


class _JSONFallbackEncoder(json.JSONEncoder):
    """
    Serialize custom datatypes and pass the rest to repr().
    """
    def default(self, obj):
        """
        Serialize obj with repr(obj) as fallback.
        """
        if isinstance(obj, ThreadLocalDict):
            return obj._dict
        else:
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


try:
    import arrow

    class TimeStamper(object):
        """
        Add a timestamp to `event_dict`.

        :param str format: strftime format string, or ``"iso"`` for `ISO 8601
            <http://en.wikipedia.org/wiki/ISO_8601>`_, or `None` for a `UNIX
            timestamp <http://en.wikipedia.org/wiki/Unix_time>`_.
        :param str tz: timezone name to use, including `local`.

        Requires `arrow <https://pypi.python.org/pypi/arrow/>`_.
        """
        def __init__(self, fmt=None, tz='UTC'):
            if fmt and fmt.lower() == 'iso':
                self._fmt = arrow.Arrow.isoformat
            elif fmt is None:
                self._fmt = attrgetter('timestamp')
            else:
                self._fmt = partial(arrow.Arrow.format, fmt=fmt)

            tzu = tz.upper()
            if fmt is None and tzu != 'UTC':
                raise ValueError('UNIX timestamps are always UTC.')

            if tzu == 'UTC':
                self._now = arrow.utcnow
            elif tzu == 'LOCAL':
                self._now = arrow.now
            else:
                self._now = partial(arrow.now, tz)

        def __call__(self, logger, name, event_dict):
            event_dict['timestamp'] = self._fmt(self._now())
            return event_dict
except ImportError:  # pragma: nocover
    class TimeStamper(object):
        """
        `arrow <https://pypi.python.org/pypi/arrow/>`_ is missing.
        """
        def __init__(self, *args, **kw):
            raise NotImplementedError(
                'TimeStamper class requires the arrow package '
                '(https://pypi.python.org/pypi/arrow/).'
            )
