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
Primitives to keep context global but thread local.
"""

import threading
import uuid


class ThreadLocalDict(object):
    """
    Wrap a dict-like class and keep the state *global* but *thread-local*.

    Attempts to re-initialize only updates the wrapped dictionary.

    Useful for short-lived threaded applications like requests in web app.

    Use :func:`wrap` to instantiate and use
    :func:`structlog.loggers.BoundLogger.new` to clear the context.
    """
    @classmethod
    def wrap(cls, dict_class):
        """
        Wrap a dict-like class and return the resulting class.

        The wrapped class will be instantiated and kept global to the current
        thread.

        :param dict_class: Class used for keeping context.

        :rtype: A class.
        """
        Wrapped = type('WrappedDict-' + str(uuid.uuid4()), (cls,), {})
        Wrapped._tl = threading.local()
        Wrapped._dict_class = dict_class
        return Wrapped

    def __init__(self, *args, **kw):
        """
        We cheat.  A context dict gets never recreated.
        """
        if args and isinstance(args[0], self.__class__):
            # our state is global, no need to look at args[0] if it's of our
            # class
            self._dict.update(**kw)
        else:
            self._dict.update(*args, **kw)

    @property
    def _dict(self):
        """
        Return or create and return the current context.
        """
        try:
            return self.__class__._tl.dict_
        except AttributeError:
            self.__class__._tl.dict_ = self.__class__._dict_class()
            return self.__class__._tl.dict_

    # Proxy methods necessary for structlog.
    def __iter__(self):
        return self._dict.__iter__()

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __len__(self):
        return self._dict.__len__()

    def __getattr__(self, name):
        method = getattr(self._dict, name)
        setattr(self, name, method)
        return method
