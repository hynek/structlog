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

import pytest
pytest.importorskip('twisted')

from structlog.twisted import LogAdapter


def _render_repr(_, __, event_dict):
    return repr(event_dict)


def test_LogAdapterFormatsLog():
    la = LogAdapter(_render_repr)
    assert "{'foo': 'bar'}" == la(None, 'msg', {'foo': 'bar'})


def test_LogAdapterTransforms_whyIntoEvent():
    """
    log.err(_stuff=exc, _why='foo') makes the output 'event="foo"'
    """
    la = LogAdapter(_render_repr)
    error = ValueError('test')
    assert ((), {
        '_stuff': error,
        '_why': "{'event': 'foo'}",
    }) == la(None, 'err', {
        '_stuff': error,
        '_why': 'foo',
        'event': None,
    })


def test_LogAdapterWorksUsualCase():
    """
    log.err(exc, _why='foo') makes the output 'event="foo"'
    """
    la = LogAdapter(_render_repr)
    error = ValueError('test')
    assert ((), {
        '_stuff': error,
        '_why': "{'event': 'foo'}",
    }) == la(None, 'err', {
        'event': error,
        '_why': 'foo',
    })


def test_LogAdapterAllKeywords():
    """
    log.err(_stuff=exc, _why='event')
    """
    la = LogAdapter(_render_repr)
    error = ValueError('test')
    assert ((), {
        '_stuff': error,
        '_why': "{'event': 'foo'}",
    }) == la(None, 'err', {
        '_stuff': error,
        '_why': 'foo',
    })


def test_LogAdapterNoFailure():
    """
    log.err('event')
    """
    la = LogAdapter(_render_repr)
    assert ((), {
        '_stuff': None,
        '_why': "{'event': 'someEvent'}",
    }) == la(None, 'err', {
        'event': 'someEvent'
    })


def test_LogAdapterNoFailureWithKeyword():
    """
    log.err(_why='event')
    """
    la = LogAdapter(_render_repr)
    assert ((), {
        '_stuff': None,
        '_why': "{'event': 'someEvent'}",
    }) == la(None, 'err', {
        '_why': 'someEvent'
    })


def test_LogAdapterCatchesConflictingEventAnd_why():
    la = LogAdapter(_render_repr)
    with pytest.raises(ValueError) as e:
        la(None, 'err', {
            'event': 'someEvent',
            '_why': 'someReason',
        })
    assert 'Both `_why` and `event` supplied.' == e.value.message
