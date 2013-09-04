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
from twisted.python.failure import Failure, NoCurrentExceptionError

from structlog.twisted import (
    BoundLogger,
    JSONRenderer,
    LogAdapter,
    _extractStuffAndWhy,
    get_logger,
)


def test_get_logger():
    assert isinstance(get_logger(), BoundLogger)


def _render_repr(_, __, event_dict):
    return repr(event_dict)


class TestExtractStuffAndWhy(object):
    def test_extractFailsOnTwoFailures(self):
        with pytest.raises(ValueError) as e:
            _extractStuffAndWhy({'_stuff': Failure(ValueError),
                                 'event': Failure(TypeError)})
        assert (
            'Both _stuff and event contain an Exception/Failure.'
            == e.value.message
        )

    def test_failsOnConflictingEventAnd_why(self):
        with pytest.raises(ValueError) as e:
            _extractStuffAndWhy({'_why': 'foo', 'event': 'bar'})
        assert (
            'Both `_why` and `event` supplied.'
            == e.value.message
        )

    def test_handlesFailures(self):
        assert (
            Failure(ValueError()), 'foo', {}
            == _extractStuffAndWhy({'_why': 'foo',
                                    '_stuff': Failure(ValueError())})
        )
        assert (
            Failure(ValueError()), 'error', {}
            == _extractStuffAndWhy({'_stuff': Failure(ValueError())})
        )

    def test_handlesMissingFailure(self):
        assert (
            (None, 'foo', {})
            == _extractStuffAndWhy({'event': 'foo'})
        )

    def test_recognizesErrorsAndCleansThem(self):
        """
        If no error is supplied, the environment is checked for one.  If one is
        found, it's used and cleared afterwards so log.err doesn't add it as
        well.
        """
        try:
            raise ValueError
        except ValueError:
            f = Failure()
            _stuff, _why, ed = _extractStuffAndWhy({'event': 'foo'})
            assert _stuff.value is f.value
            with pytest.raises(NoCurrentExceptionError):
                Failure()


class TestLogAdapter(object):
    """
    Some tests here are redundant because they predate _extractStuffAndWhy.
    """
    def test_LogAdapterFormatsLog(self):
        la = LogAdapter(_render_repr)
        assert "{'foo': 'bar'}" == la(None, 'msg', {'foo': 'bar'})

    def test_transforms_whyIntoEvent(self):
        """
        log.err(_stuff=exc, _why='foo') makes the output 'event="foo"'
        """
        la = LogAdapter(_render_repr)
        error = ValueError('test')
        rv = la(None, 'err', {
            '_stuff': error,
            '_why': 'foo',
            'event': None,
        })
        assert () == rv[0]
        assert isinstance(rv[1]['_stuff'], Failure)
        assert error == rv[1]['_stuff'].value
        assert "{'event': 'foo'}" == rv[1]['_why']

    def test_worksUsualCase(self):
        """
        log.err(exc, _why='foo') makes the output 'event="foo"'
        """
        la = LogAdapter(_render_repr)
        error = ValueError('test')
        rv = la(None, 'err', {'event': error, '_why': 'foo'})
        assert () == rv[0]
        assert isinstance(rv[1]['_stuff'], Failure)
        assert error == rv[1]['_stuff'].value
        assert "{'event': 'foo'}" == rv[1]['_why']

    def test_allKeywords(self):
        """
        log.err(_stuff=exc, _why='event')
        """
        la = LogAdapter(_render_repr)
        error = ValueError('test')
        rv = la(None, 'err', {'_stuff': error, '_why': 'foo'})
        assert () == rv[0]
        assert isinstance(rv[1]['_stuff'], Failure)
        assert error == rv[1]['_stuff'].value
        assert "{'event': 'foo'}" == rv[1]['_why']

    def test_noFailure(self):
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

    def test_noFailureWithKeyword(self):
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

    def test_catchesConflictingEventAnd_why(self):
        la = LogAdapter(_render_repr)
        with pytest.raises(ValueError) as e:
            la(None, 'err', {
                'event': 'someEvent',
                '_why': 'someReason',
            })
        assert 'Both `_why` and `event` supplied.' == e.value.message


@pytest.fixture
def jr():
    """
    A plain JSONRenderer.
    """
    return JSONRenderer()


class TestJSONRenderer(object):
    def test_dumpsKWsAreHandedThrough(self, jr):
        d = {'x': 'foo', 'a': 'bar'}
        jr_sorted = JSONRenderer(sort_keys=True)
        assert jr_sorted(None, 'err', d) != jr(None, 'err', d)

    def test_handlesMissingFailure(self, jr):
        assert '{"event": "foo"}' == jr(None, 'err', {'event': 'foo'})
        assert '{"event": "foo"}' == jr(None, 'err', {'_why': 'foo'})

    def test_msgWorksToo(self, jr):
        assert '{"event": "foo"}' == jr(None, 'msg', {'_why': 'foo'})

    def test_handlesFailure(self, jr):
        rv = jr(None, 'err', {'event': Failure(ValueError())})
        assert 'Failure: exceptions.ValueError:' in rv
        assert '"event": "error"' in rv
