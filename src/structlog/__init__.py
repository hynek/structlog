# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.


from __future__ import annotations

from structlog import (
    contextvars,
    dev,
    processors,
    stdlib,
    testing,
    threadlocal,
    tracebacks,
    types,
)
from structlog._base import BoundLoggerBase, get_context
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
from structlog._log_levels import make_filtering_bound_logger
from structlog._loggers import (
    BytesLogger,
    BytesLoggerFactory,
    PrintLogger,
    PrintLoggerFactory,
    WriteLogger,
    WriteLoggerFactory,
)
from structlog.exceptions import DropEvent
from structlog.testing import ReturnLogger, ReturnLoggerFactory


try:
    from structlog import twisted
except ImportError:
    twisted = None  # type: ignore


__title__ = "structlog"

__uri__ = "https://www.structlog.org/"

__author__ = "Hynek Schlawack"
__email__ = "hs@ox.cx"

__license__ = "MIT or Apache License, Version 2.0"
__copyright__ = "Copyright (c) 2013 " + __author__


__all__ = [
    "BoundLogger",
    "BoundLoggerBase",
    "BytesLogger",
    "BytesLoggerFactory",
    "configure_once",
    "configure",
    "contextvars",
    "dev",
    "DropEvent",
    "get_config",
    "get_context",
    "get_logger",
    "getLogger",
    "is_configured",
    "make_filtering_bound_logger",
    "PrintLogger",
    "PrintLoggerFactory",
    "processors",
    "reset_defaults",
    "ReturnLogger",
    "ReturnLoggerFactory",
    "stdlib",
    "testing",
    "threadlocal",
    "tracebacks",
    "twisted",
    "types",
    "wrap_logger",
    "WriteLogger",
    "WriteLoggerFactory",
]


def __getattr__(name: str) -> str:
    dunder_to_metadata = {
        "__version__": "version",
        "__description__": "summary",
    }
    if name not in dunder_to_metadata.keys():
        raise AttributeError(f"module {__name__} has no attribute {name}")

    import sys
    import warnings

    if sys.version_info < (3, 8):
        import importlib_metadata as metadata
    else:
        from importlib import metadata

    warnings.warn(
        f"Accessing structlog.{name} is deprecated and will be "
        "removed in a future release. Use importlib.metadata directly "
        "to query for structlog's packaging metadata.",
        DeprecationWarning,
        stacklevel=2,
    )

    return metadata.metadata("structlog")[dunder_to_metadata[name]]
