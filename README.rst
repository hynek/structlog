structlog: Structured Python Logging
====================================

.. image:: https://travis-ci.org/hynek/structlog.png?branch=master
   :target: https://travis-ci.org/hynek/structlog

.. image:: https://coveralls.io/repos/hynek/structlog/badge.png?branch=master
    :target: https://coveralls.io/r/hynek/structlog?branch=master

The purpose of ``structlog`` is to allow you to log structured_, easily parsable_ data even if your logger doesn’t support it.
Contrary to other alternatives, ``structlog`` is agnostic about the underlying logging layer and wraps whatever your preferred logger is.

The way to think about logging with structlog is that you log *events* that happen in certain *contexts*.
A context is just a dictionary of key/value pairs and one of the neat features of structlog is that you can build your context as you go and there’s no need to think about it as soon as you need to log something out.

.. code-block:: pycon

   >>> # stdlib logging boilerplate
   >>> import logging, sys
   >>> logging.basicConfig(stream=sys.stdout, format='%(message)s')
   >>> # Now let's wrap the logger and bind some values.
   >>> from structlog import BoundLogger, KeyValueRenderer
   >>> logger = logging.getLogger('example_logger')
   >>> log = BoundLogger.wrap(logger)
   >>> log = log.bind(user='anonymous', some_key=23)
   >>> # Do some application stuff like user authentication.
   >>> # As result, we have new values to bind to our logger.
   >>> log = log.bind(user='hynek', source='http', another_key=42)
   >>> log.warning('user.logged_in', happy=True)
   some_key=23 user='hynek' source='http' another_key=42 happy=True event='user.logged_in'

In other words, you tell your logger about values *as you learn about them* and it will include the information in all future log entries.
This gives you much more complete logs without boilerplate code and conditionals.

structlog allows you to choose the dictionary implementation freely and ships one particularly handy one that allows you to keep your context in a global but thread local place.
This is very handy in conjuction with multi-threaded applications like web apps:

``file1.py``

.. code-block:: python

   import logging
   import uuid

   from flask import request
   from structlog import BoundLogger, ThreadLocalDict

   from .file2 import some_function

   log = BoundLogger(logging.getLogger(__name__))

   @app.route('/login', methods=['POST', 'GET'])
   def some_route():
       log.new(
           request_id=str(uuid.uuid4()),
           method=request.method,
           path=request.path,
           username=request.cookies.get('username'),
       )
       # do something
       # ...
       log.bind(foo='bar')
       # ...
       some_function()
       # ...

   if __name__ == "__main__":
      BoundLogger.configure(
         context_class=structlog.ThreadLocalDict(dict),
      )
      app.run()

``file2.py``

.. code-block:: python

   import logging

   from structlog import BoundLogger

   log = BoundLogger.wrap(logging.getLogger(__name__))

   def some_function():
       # later then:
       log.error('user did something')
       # gives you:
       # request_id='ffcdc44f-b952-4b5f-95e6-0f1f3a9ee5fd' event='user did something' foo='bar' method='POST' path='/' username='jane'


Processors
----------

The true power of ``structlog`` lies in its *composable log processors*.
You can define a chain of callables that will get passed the wrapped logger, the name of the wrapped method, and the current context together with the current event (called ``event_dict``) as positional arguments.
The return value of each processor is passed on to the next one as ``event_dict`` until finally the return value of the last processor gets passed into the wrapped logging method.
Therefore, the last processor must adapt the ``event_dict`` into something the underlying logging method understands.

There are two special return values:

- ``False`` aborts the processor chain and the log entry is silently dropped.
- ``None`` raises an ``ValueError`` because you probably forgot to return a new value.

Additionally, the last processor can either return a string that is passed as the first (and only) positional argument to the underlying logger or a tuple of ``(args, kwargs)`` that are passed as ``log_method(*args, **kwargs)``.
Therefore ``return 'hello world'`` is a shortcut for ``return (('hello world',), {})``.

This should give you enough power to use it with any logging system.


Examples
++++++++

So you want timestamps as part of the structure of the log entry, censor passwords, filter out log entries below your log level before they even get rendered, and get your output as JSON for convenient parsing?
Here you go:

.. code-block:: pycon

   >>> import datetime
   >>> from structlog import JSONRenderer
   >>> from structlog.stdlib import filter_by_level
   >>> def add_timestamp(_, __, event_dict):
   ...     event_dict['timestamp'] = datetime.datetime.utcnow()
   ...     return event_dict
   >>> def censor_password(_, __, event_dict):
   ...     pw = event_dict.get('password')
   ...     if pw:
   ...         event_dict['password'] = '*CENSORED*'
   ...     return event_dict
   >>> log = BoundLogger.wrap(
   ...     logger,
   ...     processors=[
   ...         filter_by_level,
   ...         add_timestamp,
   ...         censor_password,
   ...         JSONRenderer(indent=1, sort_keys=True)
   ...     ]
   ... )
   >>> log.info('something.filtered')
   >>> log.warning('something.not_filtered', password='secret') # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
   {
    "event": "something.not_filtered",
    "password": "*CENSORED*",
    "timestamp": "datetime.datetime(..., ..., ..., ..., ...)"
   }


Requirements
------------

Works with Python 2.6, 2.7, 3.2, and 3.3 as well as with PyPy with no additional dependencies.
Some processors require additional packages if used.

.. _structured: http://glyph.twistedmatrix.com/2009/06/who-wants-to-know.html
.. _parsable:  http://journal.paul.querna.org/articles/2011/12/26/log-for-machines-in-json/
