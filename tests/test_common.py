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

import pytest

import structlog

from structlog.common import (
    JSONRenderer,
    _ReprFallbackEncoder,
    add_timestamp,
    format_exc_info,
    render_kv,
)


@pytest.fixture
def event_dict():
    class A(object):
        def __repr__(self):
            return '<A(\o/)>'

    return {'a': A(), 'b': [3, 4], 'x': 7, 'y': 'test', 'z': (1, 2)}


def test_render_kv(event_dict):
    assert (
        r"a=<A(\o/)> b=[3, 4] x=7 y='test' z=(1, 2)" ==
        render_kv(None, None, event_dict)
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


def test_add_timestamp():
    d = add_timestamp(None, None, {})
    assert isinstance(d['timestamp'], datetime.datetime)


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


def test_format_exception():
    pass
