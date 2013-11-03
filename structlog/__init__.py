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
Painless structured logging.
"""

from __future__ import absolute_import, division, print_function

__version__ = '0.4.0dev'


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
    BoundLogger,
    BoundLoggerBase,
    DropEvent,
    PrintLogger,
    PrintLoggerFactory,
    ReturnLogger,
    ReturnLoggerFactory,
    configure,
    configure_once,
    getLogger,
    get_logger,
    processors,
    reset_defaults,
    stdlib,
    threadlocal,
    twisted,
    wrap_logger,
]
