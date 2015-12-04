# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Compatibility utilities.
"""

from __future__ import absolute_import, division, print_function

import abc
import sys
import types

from six import (
    PY2, PY3, string_types, integer_types, class_types, text_type
)


try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO  # flake8: noqa

if sys.version_info[:2] == (2, 6):
    try:
        from ordereddict import OrderedDict
    except ImportError:  # pragma: nocover
        class OrderedDict(object):
            def __init__(self, *args, **kw):
                raise NotImplementedError(
                    'The ordereddict package is needed on Python 2.6. '
                    'See <http://www.structlog.org/en/latest/'
                    'installation.html>.'
                )
else:
    from collections import OrderedDict
