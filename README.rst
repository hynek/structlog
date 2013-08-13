structlog: Structured Python logging.
=====================================

.. image:: https://travis-ci.org/hynek/structlog.png?branch=master
   :target: https://travis-ci.org/hynek/structlog

.. image:: https://coveralls.io/repos/hynek/structlog/badge.png?branch=master
    :target: https://coveralls.io/r/hynek/structlog?branch=master

The purpose of ``structlog`` is to allow you to easily log structured, easily parsable data even if your logger doesn’t support it.
Contrary to other alternatives, ``structlog`` is agnostic about the underlying logging layer and wraps whatever your preferred logger is.

Each log entry is a dictionary until it needs to be transformed into something that is understood by your logger – we call it an ``event_dict``.

A nice feature is that you can build your log entry incrementally by binding values to your logger:

.. code-block:: pycon

   >>> # stdlib logging boilerplate
   >>> import logging, sys
   >>> logging.basicConfig(stream=sys.stdout, format='%(message)s')
   >>> # Now let's wrap the logger and bind some values.
   >>> from structlog import BoundLog
   >>> logger = logging.getLogger('example_logger')
   >>> log = BoundLog.fromLogger(logger).bind(user='anonymous', some_key=23)
   >>> # Do some application stuff like user authentication.
   >>> # As result, we have new values to bind to our logger.
   >>> log = log.bind(user='hynek', source='http', another_key=42)
   >>> log.warning('user.logged_in', happy=True)
   another_key=42 event='user.logged_in' happy=True some_key=23 source='http' user='hynek'

In other words, you tell your logger about values *as you learn about them* and it will include the information in all future log entries.
This gives you much more complete logs without boilerplate code and conditionals.

Especially in conjunction with web frameworks logging gets much more pleasing:

.. code-block:: python

   from flask import request


   @app.route('/login', methods=['POST', 'GET'])
   def some_route():
       log = BoundLog.fromLogger(logger).bind(
           method=request.method,
           path=request.path,
           username=request.cookies.get('username'),
       )
       # do something
       # ...
       log = log.bind(foo='bar')
       # ...
       # later then:
       log.error('user did something')
       # gives you:
       # event='user did something' foo='bar' method='POST' path='/' username='jane'


Processors
----------

The true power of ``structlog`` lies in its *composable log processors*.
You can define a chain of callables that will get passed the wrapped logger, the name of the wrapped method, and the current ``event_dict`` as positional arguments.
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
   >>> log = BoundLog.fromLogger(
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
