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
    _ReprFallbackEncoder,
    format_exc_info,
)


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


def test_JSONRenderer_renders_json(event_dict):
    assert (
        r'{"a": "<A(\\o/)>", "b": [3, 4], "x": 7, "y": "test", "z": [1, 2]}' ==
        JSONRenderer(sort_keys=True)(None, None, event_dict)
    )


def test_ReprFallbackEncoder_falls_back():
    s = json.dumps({'date': datetime.date(1980, 3, 25)},
                   cls=_ReprFallbackEncoder,)

    assert '{"date": "datetime.date(1980, 3, 25)"}' == s


def test_TimeStamperDisallowsNonUTCUNIXTimestamps():
    with pytest.raises(ValueError) as e:
        TimeStamper(tz='CEST')
    assert 'UNIX timestamps are always UTC.' == e.value.args[0]


@freeze_time('1980-03-25 16:00:00', tz_offset=1)
def test_TimeStamperInsertsUTCUNIXTimestampByDefault():
    ts = TimeStamper()
    d = ts(None, None, {})
    assert 322848000 == d['timestamp']


@freeze_time('1980-03-25 16:00:00')
def test_TimeStamperTransplantsCorrectly():
    ts = TimeStamper(fmt='iso', tz='CET')
    d = ts(None, None, {})
    assert '1980-03-25T17:00:00+01:00' == d['timestamp']


def test_TimeStamperTransplantsCorrectlyToLocal():
    ts = TimeStamper(fmt='iso', tz='lOcAl')
    assert arrow.now == ts._now


@freeze_time('1980-03-25 16:00:00')
def test_TimeStamperFormats():
    ts = TimeStamper(fmt='YYYY')
    d = ts(None, None, {})
    assert '1980' == d['timestamp']


def test_format_exc_info_formats_tuple(monkeypatch):
    monkeypatch.setattr(structlog.common,
                        '_format_exception',
                        lambda exc_info: exc_info)
    d = format_exc_info(None, None, {'exc_info': (None, None, 42)})
    assert {'exception': (None, None, 42)} == d


def test_format_exc_info_gets_exc_info_on_bool():
    # monkeypatching sys.exc_info makes currently py.test return 1 on success.
    try:
        raise ValueError('test')
    except ValueError:
        d = format_exc_info(None, None, {'exc_info': True})
    assert 'exc_info' not in d
    assert 'raise ValueError(\'test\')\nValueError: test' in d['exception']


def test_UnicodeEncoder_encodes():
    ue = UnicodeEncoder()
    assert {'foo': b'b\xc3\xa4r'} == ue(None, None, {'foo': u('b\xe4r')})


def test_UnicodeEncoder_passes_arguments():
    ue = UnicodeEncoder('latin1', 'xmlcharrefreplace')
    assert {'foo': b'&#8211;'} == ue(None, None, {'foo': u('\u2013')})
