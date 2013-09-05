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

import pytest
import threading

from structlog.threadlocal import wrap_dict


@pytest.fixture
def D():
    """
    Returns a dict wrapped in _ThreadLocalDict.
    """
    return wrap_dict(dict)


class TestThreadLocalDict(object):
    def test_wrap_returns_distinct_classes(self):
        D1 = wrap_dict(dict)
        D2 = wrap_dict(dict)
        assert D1 != D2
        assert D1 is not D2
        D1.x = 42
        D2.x = 23
        assert D1.x != D2.x

    def test_is_thread_local(self, D):
        class TestThread(threading.Thread):
            def __init__(self, d):
                self._d = d
                threading.Thread.__init__(self)

            def run(self):
                assert 'x' not in self._d._dict
                self._d['x'] = 23
        d = wrap_dict(dict)()
        d['x'] = 42
        t = TestThread(d)
        t.start()
        t.join()
        assert 42 == d._dict['x']

    def test_context_is_global_to_thread(self, D):
        d1 = D({'a': 42})
        d2 = D({'b': 23})
        d3 = D()
        assert {'a': 42, 'b': 23} == d1._dict == d2._dict == d3._dict
        assert d1 == d2 == d3
        D_ = wrap_dict(dict)
        d_ = D_({'a': 42, 'b': 23})
        assert d1 != d_

    def test_init_with_itself_works(self, D):
        d = D({'a': 42})
        assert {'a': 42, 'b': 23} == D(d, b=23)._dict

    def test_iter_works(self, D):
        d = D({'a': 42})
        assert ['a'] == list(iter(d))

    def test_non_dunder_proxy_works(self, D):
        d = D({'a': 42})
        assert 1 == len(d)
        d.clear()
        assert 0 == len(d)

    def test_repr(self, D):
        r = repr(D({'a': 42}))
        assert r.startswith('<WrappedDict-')
        assert r.endswith("({'a': 42})>")
