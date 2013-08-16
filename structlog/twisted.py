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

from twisted.python.failure import Failure


class LogAdapter(object):
    """
    Make a wrapped `twisted.python.log.err` behave as expected.
    """
    def __init__(self, dictFormatter):
        """
        :param dictFormatter: A processor used to format the log message.
        """
        self._dictFormatter = dictFormatter

    def __call__(self, logger, name, eventDict):
        if name == 'err':
            # This aspires to handle the following cases correctly:
            #   - log.err(failure, _why='event', **kw)
            #   - log.err('event', **kw)
            #   - log.err(_stuff=failure, _why='event', **kw)
            failure = eventDict.pop('_stuff', None)
            event = eventDict.pop('event', None)
            _why = eventDict.pop('_why', None)
            if not failure and isinstance(event, (Exception, Failure)):
                failure = event
                event = None
            # `log.err('event', _why='alsoEvent')` is ambiguous.
            if event and _why:
                raise ValueError('Both `_why` and `event` supplied.')
            eventDict['event'] = event or _why
            return ((), {
                '_stuff': failure,
                '_why': self._dictFormatter(logger, name, eventDict),
            })
        else:
            return self._dictFormatter(logger, name, eventDict)
