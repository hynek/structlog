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

from __future__ import absolute_import, division, print_function

import io
import json
import sys
import traceback

from functools import wraps


class BoundLog(object):
    def __init__(self, logger, processors, event_dict):
        """
        Use `fromLogger()`.
        """
        self._logger = logger
        self._event_dict = event_dict
        self._processors = processors

    @classmethod
    def fromLogger(cls, logger, processors=None):
        """
        Create a new BoundLog for `logger`.

        :param logger: An instance of a logger whose method calls will be
            wrapped.
        :param list processors: List of processors.

        :rtype: BoundLog
        """
        return cls(
            logger,
            processors or [
                format_exc_info,
                JSONRenderer(sort_keys=True, indent=4),
            ], {}
        )

    def bind(self, **kw):
        event_dict = dict(self._event_dict, **kw)
        return self.__class__(self._logger, self._processors, event_dict)

    def __getattr__(self, name):
        log_meth = getattr(self._logger, name)

        @wraps(log_meth)
        def wrapped(event, **kw):
            """
            Before calling actual logger method, transform the accumulated
            `event_dict` together with the event itself using the processor
            chain.
            """
            res = dict(self._event_dict, event=event, **kw)
            for processor in self._processors:
                res = processor(self._logger, name, res)
                if res is None:
                    raise ValueError('Log processor returned None.')
                elif res is False:
                    return
            return log_meth(res)
        return wrapped


class JSONRenderer(object):
    def __init__(self, **json_kw):
        self._json_kw = json_kw

    def __call__(self, logger, name, event_dict):
        return json.dumps(event_dict, cls=_ReprFallbackEncoder,
                          **self._json_kw)


class _ReprFallbackEncoder(json.JSONEncoder):
    """
    A JSONEncoder that will use the repr(obj) as the default serialization
    for objects that the base JSONEncoder does not know about.

    This will ensure that even log messages that include unserializable objects
    (like from 3rd party libraries) will still have reasonable representations
    in the logged JSON and will actually be logged and not discarded by the
    logging system because of a formatting error.
    """
    def default(self, obj):
        """
        Serialize obj as repr(obj).
        """
        return repr(obj)


def _format_exception(exc_info):
    """
    Shamelessly stolen from stdlib's logging module.
    """
    sio = io.StringIO()
    tb = exc_info[2]
    traceback.print_exception(exc_info[0], exc_info[1], tb, None, sio)
    s = sio.getvalue()
    sio.close()
    if s[-1:] == "\n":
        s = s[:-1]
    return s


def add_timestamp(logger, name, event_dict):
    """
    Add a UTC timestamp.
    """
    import datetime
    event_dict['timestamp'] = datetime.datetime.utcnow()
    return event_dict


def format_exc_info(logger, name, event_dict):
    """
    Handle an `exc_info` field like stdlib logging:

    - if it's a tuple, render it
    - if it's true, obtain exc_info ourselve and render it
    """
    exc_info = event_dict.pop('exc_info', None)
    if exc_info:
        if not isinstance(exc_info, tuple):
            exc_info = sys.exc_info()
            event_dict['exception'] = _format_exception(exc_info)
    return event_dict
