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
Helper function for testing the deduction of stdlib logger names.

Since the logger factories are called from within structlog._config, they have
to skip a frame.  Calling them here emulates that.
"""

from __future__ import absolute_import, division, print_function


def additional_frame(callable):
    return callable()
