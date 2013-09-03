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
Common tools useful regardless of the logging framework.
"""

from __future__ import absolute_import, division, print_function

import json
import sys
import traceback
import threading

from functools import partial
from operator import attrgetter
from uuid import uuid4

from structlog._compat import StringIO, unicode_type


class KeyValueRenderer(object):
    """
    Render `event_dict` as a list of `Key=Value` pairs.
    """
    def __init__(self, sort_keys=False):
        """
        :param bool sort_keys: Whether to sort keys when formatting.
        """
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

    - if `exc_info` is a tuple, render it
    - if `exc_info` is true, obtain exc_info ourselve and render that
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


class ThreadLocalDict(object):
    """
    Wrap a dict-like class and keep the state *global* but *thread-local*.

    Attempts to re-initialize only updates the wrapped dictionary.

    Useful for short-lived threaded applications like requests in web app.

    Use :func:`wrap` to instantiate and use
    :func:`structlog.loggers.BoundLogger.new` to clear the context.
    """
    @classmethod
    def wrap(cls, dict_class):
        """
        Wrap a dict-like class and return the resulting class.

        The wrapped class will be instantiated and kept global to the current
        thread.

        :param dict_class: Class used for keeping context.

        :rtype: A class.
        """
        Wrapped = type('WrappedDict-' + str(uuid4()), (cls,), {})
        Wrapped._tl = threading.local()
        Wrapped._dict_class = dict_class
        return Wrapped

    def __init__(self, *args, **kw):
        """
        We cheat.  A context dict gets never recreated.
        """
        if args and isinstance(args[0], self.__class__):
            # our state is global, no need to look at args[0] if it's of our
            # class
            self._dict.update(**kw)
        else:
            self._dict.update(*args, **kw)

    @property
    def _dict(self):
        """
        Return or create and return the current context.
        """
        try:
            return self.__class__._tl.dict_
        except AttributeError:
            self.__class__._tl.dict_ = self.__class__._dict_class()
            return self.__class__._tl.dict_

    # Proxy methods necessary for structlog.
    def __iter__(self):
        return self._dict.__iter__()

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __len__(self):
        return self._dict.__len__()

    def __getattr__(self, name):
        method = getattr(self._dict, name)
        setattr(self, name, method)
        return method
