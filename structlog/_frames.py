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

import sys
import traceback

from structlog._compat import StringIO


def _format_exception(exc_info):
    """
    Prettyprint an `exc_info` tuple.

    Shamelessly stolen from stdlib's logging module.
    """
    sio = StringIO()
    traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], None, sio)
    s = sio.getvalue()
    sio.close()
    if s[-1:] == "\n":
        s = s[:-1]
    return s


def _find_first_app_frame_and_name(additional_ignores=None):
    """
    Remove all intra-structlog calls and return the relevant app frame.

    :param additional_ignores: Additional names with which the first frame must
        not start.
    :type additional_ignores: `list` of `str` or `None`

    :rtype: tuple of (frame, name)
    """
    ignores = ['structlog'] + (additional_ignores or [])
    f = sys._getframe()
    name = f.f_globals['__name__']
    while any(name.startswith(i) for i in ignores):
        f = f.f_back
        name = f.f_globals['__name__']
    return f, name


def _format_stack(frame):
    """
    Pretty-print the stack of `frame` like logging would.
    """
    sio = StringIO()
    sio.write('Stack (most recent call last):\n')
    traceback.print_stack(frame, file=sio)
    sinfo = sio.getvalue()
    if sinfo[-1] == '\n':
        sinfo = sinfo[:-1]
    sio.close()
    return sinfo
