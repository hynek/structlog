# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Shared test utilities.
"""

from __future__ import absolute_import, division, print_function

import pytest
import six


py3_only = pytest.mark.skipif(not six.PY3, reason="Python 3-only")
py2_only = pytest.mark.skipif(not six.PY2, reason="Python 2-only")
