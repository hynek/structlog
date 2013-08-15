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

"""
Python 2 + 3 compatibility utilities.

Heavily inspired by https://bitbucket.org/gutworth/six/ .
"""

from __future__ import absolute_import, division, print_function

import sys
import types

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


try:  # pragma: nocover
    from cStringIO import StringIO
except ImportError:  # pragma: nocover
    from io import StringIO  # flake8: noqa

if PY3:  # pragma: nocover
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes
    unicode_type = str
    u = lambda s: s
else:  # pragma: nocover
    string_types = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str
    unicode_type = unicode
    u = lambda s: unicode(s, "unicode_escape")
