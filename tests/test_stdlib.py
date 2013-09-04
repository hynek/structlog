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

import logging

from structlog.stdlib import get_logger, filter_by_level, WARN, CRITICAL


class TestGetLogger(object):
    def test_respects_name(self):
        l = get_logger('foobar')
        assert 'foobar' == l._logger.name

    def test_deduces_correct_name(self):
        l = get_logger()
        assert 'tests.test_stdlib' == l._logger.name


class TestFilterByLevel(object):
    def test_filters_lower_levels(self):
        logger = logging.Logger(__name__)
        logger.setLevel(CRITICAL)
        assert False is filter_by_level(logger, 'warn', {})

    def test_passes_higher_levels(self):
        logger = logging.Logger(__name__)
        logger.setLevel(WARN)
        event_dict = {'event': 'test'}
        assert event_dict is filter_by_level(logger, 'warn', event_dict)
        assert event_dict is filter_by_level(logger, 'error', event_dict)
