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

from __future__ import absolute_import, division, print_function


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
    Abort before it gets expensive.

    Should be the first processor if stdlib's filtering by level is used.
    """
    if logger.isEnabledFor(_nameToLevel[name]):
        return event_dict
    else:
        return False
