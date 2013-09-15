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
Generic utilities.
"""

from __future__ import absolute_import, division, print_function

import errno


def until_not_interrupted(f, *args, **kw):
    """
    Retry until *f* succeeds or an exception that isn't caused by EINTR occurs.

    :param callable f: A callable like a function.
    :param *args: Positional arguments for *f*.
    :param **kw: Keyword arguments for *f*.
    """
    while True:
        try:
            return f(*args, **kw)
        except (IOError, OSError) as e:
            if e.args[0] == errno.EINTR:
                continue
            raise
