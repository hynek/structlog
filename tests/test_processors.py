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

import datetime
import json
import sys

import pytest

from freezegun import freeze_time

import structlog

from structlog._compat import u, StringIO
from structlog.processors import (
    ExceptionPrettyPrinter,
    JSONRenderer,
    KeyValueRenderer,
    StackInfoRenderer,
    TimeStamper,
    UnicodeEncoder,
    _JSONFallbackEncoder,
    format_exc_info,
)
from structlog.threadlocal import wrap_dict


@pytest.fixture
def sio():
    return StringIO()


@pytest.fixture
def event_dict():
    class A(object):
        def __repr__(self):
            return '<A(\o/)>'

    return {'a': A(), 'b': [3, 4], 'x': 7, 'y': 'test', 'z': (1, 2)}


class TestKeyValueRenderer(object):
    def test_sort_keys(self, event_dict):
        assert (
            r"a=<A(\o/)> b=[3, 4] x=7 y='test' z=(1, 2)" ==
            KeyValueRenderer(sort_keys=True)(None, None, event_dict)
        )

    def test_order_complete(self, event_dict):
        assert (
            r"y='test' b=[3, 4] a=<A(\o/)> z=(1, 2) x=7" ==
            KeyValueRenderer(key_order=['y', 'b', 'a', 'z', 'x'])
            (None, None, event_dict)
        )

    def test_order_missing(self, event_dict):
        """
        Missing keys get rendered as None.
        """
        assert (
            r"c=None y='test' b=[3, 4] a=<A(\o/)> z=(1, 2) x=7" ==
            KeyValueRenderer(key_order=['c', 'y', 'b', 'a', 'z', 'x'])
            (None, None, event_dict)
        )

    def test_order_extra(self, event_dict):
        """
        Extra keys get sorted if sort_keys=True.
        """
        event_dict['B'] = 'B'
        event_dict['A'] = 'A'
        assert (
            r"c=None y='test' b=[3, 4] a=<A(\o/)> z=(1, 2) x=7 A='A' B='B'" ==
            KeyValueRenderer(key_order=['c', 'y', 'b', 'a', 'z', 'x'],
                             sort_keys=True)
            (None, None, event_dict)
        )

    def test_random_order(self, event_dict):
        rv = KeyValueRenderer()(None, None, event_dict)
        assert isinstance(rv, str)


class TestJSONRenderer(object):
    def test_renders_json(self, event_dict):
        assert (
            r'{"a": "<A(\\o/)>", "b": [3, 4], "x": 7, "y": "test", "z": '
            r'[1, 2]}'
            == JSONRenderer(sort_keys=True)(None, None, event_dict)
        )

    def test_FallbackEncoder_handles_ThreadLocalDictWrapped_dicts(self):
        s = json.dumps(wrap_dict(dict)({'a': 42}),
                       cls=_JSONFallbackEncoder)
        assert '{"a": 42}' == s

    def test_FallbackEncoder_falls_back(self):
        s = json.dumps({'date': datetime.date(1980, 3, 25)},
                       cls=_JSONFallbackEncoder,)

        assert '{"date": "datetime.date(1980, 3, 25)"}' == s


class TestTimeStamper(object):
    def test_disallowsNonUTCUNIXTimestamps(self):
        with pytest.raises(ValueError) as e:
            TimeStamper(utc=False)
        assert 'UNIX timestamps are always UTC.' == e.value.args[0]

    def test_insertsUTCUNIXTimestampByDefault(self):
        ts = TimeStamper()
        d = ts(None, None, {})
        # freezegun doesn't work with time.gmtime :(
        assert isinstance(d['timestamp'], int)

    @freeze_time('1980-03-25 16:00:00')
    def test_local(self):
        ts = TimeStamper(fmt='iso', utc=False)
        d = ts(None, None, {})
        assert '1980-03-25T16:00:00' == d['timestamp']

    @freeze_time('1980-03-25 16:00:00')
    def test_formats(self):
        ts = TimeStamper(fmt='%Y')
        d = ts(None, None, {})
        assert '1980' == d['timestamp']

    @freeze_time('1980-03-25 16:00:00')
    def test_adds_Z_to_iso(self):
        ts = TimeStamper(fmt='iso', utc=True)
        d = ts(None, None, {})
        assert '1980-03-25T16:00:00Z' == d['timestamp']


class TestFormatExcInfo(object):
    def test_formats_tuple(self, monkeypatch):
        monkeypatch.setattr(structlog.processors,
                            '_format_exception',
                            lambda exc_info: exc_info)
        d = format_exc_info(None, None, {'exc_info': (None, None, 42)})
        assert {'exception': (None, None, 42)} == d

    def test_gets_exc_info_on_bool(self):
        # monkeypatching sys.exc_info makes currently py.test return 1 on
        # success.
        try:
            raise ValueError('test')
        except ValueError:
            d = format_exc_info(None, None, {'exc_info': True})
        assert 'exc_info' not in d
        assert 'raise ValueError(\'test\')\nValueError: test' in d['exception']


class TestUnicodeEncoder(object):
    def test_encodes(self):
        ue = UnicodeEncoder()
        assert {'foo': b'b\xc3\xa4r'} == ue(None, None, {'foo': u('b\xe4r')})

    def test_passes_arguments(self):
        ue = UnicodeEncoder('latin1', 'xmlcharrefreplace')
        assert {'foo': b'&#8211;'} == ue(None, None, {'foo': u('\u2013')})


class TestExceptionPrettyPrinter(object):
    def test_stdout_by_default(self):
        """
        If no file is supplied, use stdout.
        """
        epp = ExceptionPrettyPrinter()
        assert sys.stdout is epp._file

    def test_prints_exception(self, sio):
        """
        If there's an `exception` key in the event_dict, just print it out.
        This happens if `format_exc_info` was run before us in the chain.
        """
        epp = ExceptionPrettyPrinter(file=sio)
        try:
            raise ValueError
        except ValueError:
            ed = format_exc_info(None, None, {'exc_info': True})
        epp(None, None, ed)

        out = sio.getvalue()
        assert 'test_prints_exception' in out
        assert 'raise ValueError' in out

    def test_removes_exception_after_printing(self, sio):
        """
        After pretty printing `exception` is removed from the event_dict.
        """
        epp = ExceptionPrettyPrinter(sio)
        try:
            raise ValueError
        except ValueError:
            ed = format_exc_info(None, None, {'exc_info': True})
        assert 'exception' in ed
        new_ed = epp(None, None, ed)
        assert 'exception' not in new_ed

    def test_handles_exc_info(self, sio):
        """
        If `exc_info` is passed in, it behaves like `format_exc_info`.
        """
        epp = ExceptionPrettyPrinter(sio)
        try:
            raise ValueError
        except ValueError:
            epp(None, None, {'exc_info': True})

        out = sio.getvalue()
        assert 'test_handles_exc_info' in out
        assert 'raise ValueError' in out

    def test_removes_exc_info_after_printing(self, sio):
        """
        After pretty printing `exception` is removed from the event_dict.
        """
        epp = ExceptionPrettyPrinter(sio)
        try:
            raise ValueError
        except ValueError:
            ed = epp(None, None, {'exc_info': True})
        assert 'exc_info' not in ed

    def test_nop_if_no_exception(self, sio):
        """
        If there is no exception, don't print anything.
        """
        epp = ExceptionPrettyPrinter(sio)
        epp(None, None, {})
        assert '' == sio.getvalue()


@pytest.fixture
def sir():
    return StackInfoRenderer()


class TestStackInfoRenderer(object):
    def test_removes_stack_info(self, sir):
        """
        The `stack_info` key is removed from `event_dict`.
        """
        ed = sir(None, None, {'stack_info': True})
        assert 'stack_info' not in ed

    def test_adds_stack_if_asked(self, sir):
        """
        If `stack_info` is true, `stack` is added.
        """
        ed = sir(None, None, {'stack_info': True})
        assert 'stack' in ed

    def test_renders_correct_stack(self, sir):
        ed = sir(None, None, {'stack_info': True})
        assert "ed = sir(None, None, {'stack_info': True})" in ed['stack']
