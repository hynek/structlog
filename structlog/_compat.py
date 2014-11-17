# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

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
