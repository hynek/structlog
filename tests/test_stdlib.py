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

import os

import logging

import pytest

from structlog._exc import DropEvent
from structlog._loggers import ReturnLogger
from structlog.stdlib import (
    BoundLogger,
    CRITICAL,
    LoggerFactory,
    WARN,
    filter_by_level,
    FixedFindCallerLogger,
)

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
    def test_deduces_correct_name(self):
        """
        The factory isn't called directly but from structlog._config so
        deducing has to be slightly smarter.
        """
        assert 'tests.additional_frame' == (
            additional_frame(LoggerFactory()).name
        )
        assert 'tests.test_stdlib' == LoggerFactory()().name


    def test_deduces_correct_caller(self):
        logger = FixedFindCallerLogger('test')
        file_name, line_number, func_name = logger.findCaller()
        assert file_name == os.path.realpath(__file__)
        assert func_name == 'test_deduces_correct_caller'
        file_name, line_number, func_name = additional_frame(logger.findCaller)
        assert file_name.endswith('additional_frame.py')
        assert func_name == 'additional_frame'


    def test_sets_correct_logger(self):
        original_class = logging.getLoggerClass()
        try:
            logging.setLoggerClass(logging.Logger)
            LoggerFactory()
            assert logging.getLoggerClass() is FixedFindCallerLogger
            logging.setLoggerClass(logging.Logger)
            LoggerFactory(fix_find_caller=False)
            assert logging.getLoggerClass() is logging.Logger
        finally:
            logging.setLoggerClass(original_class)


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
        def return_method_name(_, method_name, __):
            return method_name
        bl = BoundLogger(ReturnLogger(), [return_method_name], {})
        assert method_name == getattr(bl, method_name)('event')
