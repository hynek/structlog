# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

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
