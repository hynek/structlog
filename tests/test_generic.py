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

from structlog._config import _CONFIG
from structlog._generic import BoundLogger
from structlog._loggers import ReturnLogger


class TestLogger(object):
    def log(self, msg):
        return 'log', msg

    def gol(self, msg):
        return 'gol', msg


class TestGenericBoundLogger(object):
    def test_caches(self):
        """
        __getattr__() gets called only once per logger method.
        """
        b = BoundLogger(
            ReturnLogger(),
            _CONFIG.default_processors,
            _CONFIG.default_context_class(),
        )
        assert 'msg' not in b.__dict__
        b.msg('foo')
        assert 'msg' in b.__dict__

    def test_proxies_anything(self):
        """
        Anything that isn't part of BoundLoggerBase gets proxied to the correct
        wrapped logger methods.
        """
        b = BoundLogger(
            ReturnLogger(),
            _CONFIG.default_processors,
            _CONFIG.default_context_class(),
        )
        assert 'log', 'foo' == b.log('foo')
        assert 'gol', 'bar' == b.gol('bar')
