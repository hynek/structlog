# -*- coding: utf-8 -*-

# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import absolute_import, division, print_function

import pytest

from structlog import _config, testing


class TestCaptureLogs(object):
    @classmethod
    def teardown_class(cls):
        _config.reset_defaults()

    def test_captures_logs(self):
        with testing.capture_logs() as logs:
            _config.get_logger().bind(x="y").info("hello")
            _config.get_logger().bind(a="b").info("goodbye")
        assert [
            {"event": "hello", "log_level": "info", "x": "y"},
            {"a": "b", "event": "goodbye", "log_level": "info"},
        ] == logs

    def get_active_procs(self):
        return _config.get_config()["processors"]

    def test_restores_processors_on_success(self):
        orig_procs = self.get_active_procs()
        with testing.capture_logs():
            assert orig_procs is not self.get_active_procs()
        assert orig_procs is self.get_active_procs()

    def test_restores_processors_on_error(self):
        orig_procs = self.get_active_procs()
        with pytest.raises(NotImplementedError):
            with testing.capture_logs():
                raise NotImplementedError("from test")
        assert orig_procs is self.get_active_procs()
