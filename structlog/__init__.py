# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Structured logging for Python.
"""

from __future__ import absolute_import, division, print_function

__version__ = "15.0.0.dev0"

__title__ = "structlog"
__description__ = "Structured Logging in Python"
__uri__ = "http://www.structlog.org/"

__author__ = "Hynek Schlawack"
__email__ = "hs@ox.cx"

__license__ = "MIT or Apache License, Version 2.0"
__copyright__ = "Copyright (c) 2013-2015 {0}".format(__author__)


from structlog import (
    processors,
    stdlib,
    threadlocal,
)
from structlog._base import (
    BoundLoggerBase,
)
from structlog._config import (
    configure,
    configure_once,
    getLogger,
    get_logger,
    reset_defaults,
    wrap_logger,
)
from structlog._exc import (
    DropEvent,
)
from structlog._generic import (
    BoundLogger
)
from structlog._loggers import (
    PrintLogger,
    PrintLoggerFactory,
    ReturnLogger,
    ReturnLoggerFactory,
)


try:
    from structlog import twisted
except ImportError:  # pragma: nocover
    twisted = None


__all__ = [
    'BoundLogger',
    'BoundLoggerBase',
    'DropEvent',
    'PrintLogger',
    'PrintLoggerFactory',
    'ReturnLogger',
    'ReturnLoggerFactory',
    'configure',
    'configure_once',
    'getLogger',
    'get_logger',
    'processors',
    'reset_defaults',
    'stdlib',
    'threadlocal',
    'twisted',
    'wrap_logger',
]
