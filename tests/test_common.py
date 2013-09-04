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

import datetime
import json

import arrow
import pytest

from freezegun import freeze_time

import structlog

from structlog._compat import u
from structlog.common import (
    JSONRenderer,
    KeyValueRenderer,
    TimeStamper,
    UnicodeEncoder,
    _JSONFallbackEncoder,
    format_exc_info,
)
from structlog.threadlocal import ThreadLocalDict


@pytest.fixture
def event_dict():
    class A(object):
        def __repr__(self):
            return '<A(\o/)>'

    return {'a': A(), 'b': [3, 4], 'x': 7, 'y': 'test', 'z': (1, 2)}


def test_KeyValueRenderer(event_dict):
    assert (
        r"a=<A(\o/)> b=[3, 4] x=7 y='test' z=(1, 2)" ==
        KeyValueRenderer(sort_keys=True)(None, None, event_dict)
    )


class TestJSONRenderer(object):
    def test_renders_json(self, event_dict):
        assert (
            r'{"a": "<A(\\o/)>", "b": [3, 4], "x": 7, "y": "test", "z": '
            r'[1, 2]}'
            == JSONRenderer(sort_keys=True)(None, None, event_dict)
        )

    def test_FallbackEncoder_handles_ThreadLocalDictWrapped_dicts(self):
        s = json.dumps(ThreadLocalDict.wrap(dict)({'a': 42}),
                       cls=_JSONFallbackEncoder)
        assert '{"a": 42}' == s

    def test_FallbackEncoder_falls_back(self):
        s = json.dumps({'date': datetime.date(1980, 3, 25)},
                       cls=_JSONFallbackEncoder,)

        assert '{"date": "datetime.date(1980, 3, 25)"}' == s


class TestTimeStamper(object):
    def test_disallowsNonUTCUNIXTimestamps(self):
        with pytest.raises(ValueError) as e:
            TimeStamper(tz='CEST')
        assert 'UNIX timestamps are always UTC.' == e.value.args[0]

    @freeze_time('1980-03-25 16:00:00', tz_offset=1)
    def test_insertsUTCUNIXTimestampByDefault(self):
        ts = TimeStamper()
        d = ts(None, None, {})
        assert 322848000 == d['timestamp']

    @freeze_time('1980-03-25 16:00:00')
    def test_transplantsCorrectly(self):
        ts = TimeStamper(fmt='iso', tz='CET')
        d = ts(None, None, {})
        assert '1980-03-25T17:00:00+01:00' == d['timestamp']

    def test_transplantsCorrectlyToLocal(self):
        ts = TimeStamper(fmt='iso', tz='lOcAl')
        assert arrow.now == ts._now

    @freeze_time('1980-03-25 16:00:00')
    def test_formats(self):
        ts = TimeStamper(fmt='YYYY')
        d = ts(None, None, {})
        assert '1980' == d['timestamp']


class TestFormatExcInfo(object):
    def test_formats_tuple(self, monkeypatch):
        monkeypatch.setattr(structlog.common,
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
