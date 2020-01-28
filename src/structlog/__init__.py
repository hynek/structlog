# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Structured logging for Python.
"""


from structlog import dev, processors, stdlib, testing, threadlocal
from structlog._base import BoundLoggerBase
from structlog._config import (
    configure,
    configure_once,
    get_config,
    get_logger,
    getLogger,
    is_configured,
    reset_defaults,
    wrap_logger,
)
from structlog._generic import BoundLogger
from structlog._loggers import PrintLogger, PrintLoggerFactory
from structlog.exceptions import DropEvent
from structlog.testing import ReturnLogger, ReturnLoggerFactory


try:
    from structlog import twisted
except ImportError:  # pragma: nocover
    twisted = None


__version__ = "20.2.0.dev0"

__title__ = "structlog"
__description__ = "Structured Logging for Python"
__uri__ = "https://www.structlog.org/"

__author__ = "Hynek Schlawack"
__email__ = "hs@ox.cx"

__license__ = "MIT or Apache License, Version 2.0"
__copyright__ = "Copyright (c) 2013 " + __author__


__all__ = [
    "BoundLogger",
    "BoundLoggerBase",
    "DropEvent",
    "PrintLogger",
    "PrintLoggerFactory",
    "ReturnLogger",
    "ReturnLoggerFactory",
    "configure",
    "configure_once",
    "dev",
    "getLogger",
    "get_config",
    "get_logger",
    "is_configured",
    "processors",
    "reset_defaults",
    "stdlib",
    "testing",
    "threadlocal",
    "twisted",
    "wrap_logger",
]
