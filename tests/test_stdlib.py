# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import absolute_import, division, print_function

import os

import logging

import pytest
from pretend import call_recorder

from structlog._exc import DropEvent
from structlog._loggers import ReturnLogger
from structlog.stdlib import (
    BoundLogger,
    CRITICAL,
    LoggerFactory,
    WARN,
    filter_by_level,
    _FixedFindCallerLogger,
)
from structlog._compat import PY2

from .additional_frame import additional_frame


def build_bl(logger=None, processors=None, context=None):
    """
    Convenience function to build BoundLogger with sane defaults.
    """
    return BoundLogger(
        logger or ReturnLogger(),
        processors,
        {}
    )


class TestLoggerFactory(object):
    def setup_method(self, method):
        """
        The stdlib logger factory modifies global state to fix caller
        identification.
        """
        self.original_logger = logging.getLoggerClass()

    def teardown_method(self, method):
        logging.setLoggerClass(self.original_logger)

    def test_deduces_correct_name(self):
        """
        The factory isn't called directly but from structlog._config so
        deducing has to be slightly smarter.
        """
        assert 'tests.additional_frame' == (
            additional_frame(LoggerFactory()).name
        )
        assert 'tests.test_stdlib' == LoggerFactory()().name

    def test_ignores_frames(self):
        """
        The name guesser walks up the frames until it reaches a frame whose
        name is not from structlog or one of the configurable other names.
        """
        assert '__main__' == additional_frame(LoggerFactory(
            ignore_frame_names=['tests.', '_pytest.'])
        ).name

    def test_deduces_correct_caller(self):
        logger = _FixedFindCallerLogger('test')
        file_name, line_number, func_name = logger.findCaller()[:3]
        assert file_name == os.path.realpath(__file__)
        assert func_name == 'test_deduces_correct_caller'

    @pytest.mark.skipif(PY2, reason="Py3-only")
    def test_stack_info(self):
        logger = _FixedFindCallerLogger('test')
        testing, is_, fun, stack_info = logger.findCaller(stack_info=True)
        assert 'testing, is_, fun' in stack_info

    @pytest.mark.skipif(PY2, reason="Py3-only")
    def test_no_stack_info_by_default(self):
        logger = _FixedFindCallerLogger('test')
        testing, is_, fun, stack_info = logger.findCaller()
        assert None is stack_info

    def test_find_caller(self, monkeypatch):
        logger = LoggerFactory()()
        log_handle = call_recorder(lambda x: None)
        monkeypatch.setattr(logger, 'handle', log_handle)
        logger.error('Test')
        log_record = log_handle.calls[0].args[0]
        assert log_record.funcName == 'test_find_caller'
        assert log_record.name == __name__
        assert log_record.filename == os.path.basename(__file__)

    def test_sets_correct_logger(self):
        assert logging.getLoggerClass() is logging.Logger
        LoggerFactory()
        assert logging.getLoggerClass() is _FixedFindCallerLogger

    def test_positional_argument_avoids_guessing(self):
        """
        If a positional argument is passed to the factory, it's used as the
        name instead of guessing.
        """
        l = LoggerFactory()('foo')
        assert 'foo' == l.name


class TestFilterByLevel(object):
    def test_filters_lower_levels(self):
        logger = logging.Logger(__name__)
        logger.setLevel(CRITICAL)
        with pytest.raises(DropEvent):
            filter_by_level(logger, 'warn', {})

    def test_passes_higher_levels(self):
        logger = logging.Logger(__name__)
        logger.setLevel(WARN)
        event_dict = {'event': 'test'}
        assert event_dict is filter_by_level(logger, 'warn', event_dict)
        assert event_dict is filter_by_level(logger, 'error', event_dict)


class TestBoundLogger(object):
    @pytest.mark.parametrize(('method_name'), [
        'debug', 'info', 'warning', 'error', 'critical',
    ])
    def test_proxies_to_correct_method(self, method_name):
        """
        The basic proxied methods are proxied to the correct counterparts.
        """
        def return_method_name(_, method_name, __):
            return method_name
        bl = BoundLogger(ReturnLogger(), [return_method_name], {})
        assert method_name == getattr(bl, method_name)('event')

    def test_exception_exc_info(self):
        """
        BoundLogger.exception sets exc_info=True.
        """
        bl = BoundLogger(ReturnLogger(), [], {})
        assert ((),
                {"exc_info": True, "event": "event"}) == bl.exception('event')

    def test_exception_maps_to_error(self):
        def return_method_name(_, method_name, __):
            return method_name
        bl = BoundLogger(ReturnLogger(), [return_method_name], {})
        assert "error" == bl.exception("event")
