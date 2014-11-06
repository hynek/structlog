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

import errno

import pytest

from pretend import raiser

from structlog._utils import until_not_interrupted


class TestUntilNotInterrupted(object):
    def test_passes_arguments_and_returns_return_value(self):
        def returner(*args, **kw):
            return args, kw
        assert ((42,), {'x': 23}) == until_not_interrupted(returner, 42, x=23)

    def test_leaves_unrelated_exceptions_through(self):
        exc = IOError
        with pytest.raises(exc):
            until_not_interrupted(raiser(exc('not EINTR')))

    def test_retries_on_EINTR(self):
        calls = [0]

        def raise_on_first_three():
            if calls[0] < 3:
                calls[0] += 1
                raise IOError(errno.EINTR)

        until_not_interrupted(raise_on_first_three)

        assert 3 == calls[0]
