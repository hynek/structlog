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

from pretend import stub

from structlog.loggers import (
    BoundLogger, NOPLogger, _GLOBAL_NOP_LOGGER, BaseLogger
)


def test_binds_independently():
    logger = stub(msg=lambda event: event, err=lambda event: event)
    b = BoundLogger.fromLogger(logger)
    b = b.bind(x=42, y=23)
    b1 = b.bind(foo='bar')
    assert "event='event1' foo='bar' x=42 y=23 z=1" == b1.msg('event1', z=1)
    assert "event='event2' foo='bar' x=42 y=23 z=0" == b1.err('event2', z=0)
    b2 = b.bind(foo='qux')
    assert "event='event3' foo='qux' x=42 y=23 z=2" == b2.msg('event3', z=2)
    assert "event='event4' foo='qux' x=42 y=23 z=3" == b2.err('event4', z=3)


def test_processor_returning_none_raises_valueerror():
    logger = stub(msg=lambda event: event)
    b = BoundLogger.fromLogger(logger, processors=[lambda *_: None])
    with pytest.raises(ValueError):
        b.msg('boom')


def test_processor_returning_false_silently_aborts_chain(capsys):
    logger = stub(msg=lambda event: event)
    # The 2nd processor would raise a ValueError if reached.
    b = BoundLogger.fromLogger(logger, processors=[lambda *_: False,
                                                   lambda *_: None])
    b.msg('silence!')
    assert ('', '') == capsys.readouterr()


def test_processor_can_return_both_str_and_tuple():
    logger = stub(msg=lambda args, **kw: (args, kw))
    b1 = BoundLogger.fromLogger(logger, processors=[lambda *_: 'foo'])
    b2 = BoundLogger.fromLogger(logger, processors=[lambda *_: (('foo',), {})])
    assert b1.msg('foo') == b2.msg('foo')


def test_NOPLogger_returns_itself_on_bind():
    nl = NOPLogger()
    assert nl is nl.bind(foo=42)


def test_BoundLogger_returns_GLOBAL_NOP_LOGGER_if_bind_filter_matches():
    def filter_throw_away(*_):
        return False

    b = BoundLogger.fromLogger(None, bind_filter=filter_throw_away)
    nl = b.bind(foo=42)
    assert nl == _GLOBAL_NOP_LOGGER
    # `logger` is None, so we get an AttributeError if the following call
    # doesn't get intercepted.
    nl.info('should not blow up')


def test_meta():
    """
    Class hierarchy is sound.
    """
    assert issubclass(BoundLogger, BaseLogger)
    assert isinstance(BoundLogger.fromLogger(None), BaseLogger)
    assert issubclass(NOPLogger, BaseLogger)
    assert isinstance(_GLOBAL_NOP_LOGGER, BaseLogger)
