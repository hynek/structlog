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
Processors and helpers specific to the `logging module
<http://docs.python.org/2/library/logging.html>`_ from the `Python standard
library <http://docs.python.org/>`_.
"""

from __future__ import absolute_import, division, print_function

import logging
import sys

from structlog import DropEvent


class LoggerFactory(object):
    """
    Build a standard library logger when an *instance* is called.

    Usage:
        configure(logger_class=structlog.stdlib.LoggerFactory())
    """
    def __call__(self):
        """
        Deduces the caller's module name and create a stdlib logger.

        :rtype: `logging.Logger`
        """
        return logging.getLogger(
            sys._getframe().f_back.f_back.f_globals['__name__']
        )


# Adapted from the stdlib

CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

_nameToLevel = {
    'critical': CRITICAL,
    'error': ERROR,
    'warn': WARNING,
    'warning': WARNING,
    'info': INFO,
    'debug': DEBUG,
    'notset': NOTSET,
}


def filter_by_level(logger, name, event_dict):
    """
    Check whether logging is configured to accept messages from this log level.

    Should be the first processor if stdlib's filtering by level is used so
    possibly expensive processors like exception formatters are avoided in the
    first place..
    """
    if logger.isEnabledFor(_nameToLevel[name]):
        return event_dict
    else:
        raise DropEvent
