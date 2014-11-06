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

Derived from MIT-licensed https://bitbucket.org/gutworth/six/ which is
Copyright 2010-2013 by Benjamin Peterson.
"""

from __future__ import absolute_import, division, print_function

import abc
import sys
import types

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO  # flake8: noqa

if sys.version_info[:2] == (2, 6):
    try:
        from ordereddict import OrderedDict
    except ImportError:
        class OrderedDict(object):
            def __init__(self, *args, **kw):
                raise NotImplementedError(
                    'The ordereddict package is needed on Python 2.6. '
                    'See <http://www.structlog.org/en/latest/'
                    'installation.html>.'
                )
else:
    from collections import OrderedDict

if PY3:
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes
    unicode_type = str
    u = lambda s: s
else:
    string_types = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str
    unicode_type = unicode
    u = lambda s: unicode(s, "unicode_escape")

def with_metaclass(meta, *bases):
    """
    Create a base class with a metaclass.
    """
    return meta("NewBase", bases, {})
