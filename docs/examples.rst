.. _examples:

Examples
========

This chapter is intended to give you a taste of realistic usage of ``structlog``.


.. _flask-example:

Flask and Thread Local Data
---------------------------

In the simplest case, you bind a unique request ID to every incoming request so you can easily see which log entries belong to which request.

.. literalinclude:: code_examples/flask_/webapp.py
   :language: python

``some_module.py``

.. literalinclude:: code_examples/flask_/some_module.py
   :language: python

While wrapped loggers are *immutable* by default, this example demonstrates how to circumvent that using a thread local dict implementation for context data for convenience (hence the requirement for using `new()` for re-initializing the logger).

Please note that :class:`structlog.stdlib.LoggerFactory` is a totally magic-free class that just deduces the name of the caller's module and does a :func:`logging.getLogger` with it.
It's used by :func:`structlog.get_logger` to rid you of logging boilerplate in application code.
If you prefer to name your standard library loggers explicitly, a positional argument to :func:`~structlog.get_logger` gets passed to the factory and used as the name.


.. _twisted-example:

Twisted, and Logging Out Objects
--------------------------------

If you prefer to log less but with more context in each entry, you can bind everything important to your logger and log it out with each log entry.


.. literalinclude:: code_examples/twisted_echo.py
   :language: python

gives you something like:

.. code:: text

  ... peer='127.0.0.1' connection_id='1c6c0cb5-...' count=1 data='123\n' event='echoed data!'
  ... peer='127.0.0.1' connection_id='1c6c0cb5-...' count=2 data='456\n' event='echoed data!'
  ... peer='127.0.0.1' connection_id='1c6c0cb5-...' count=3 data='foo\n' event='echoed data!'
  ... peer='10.10.0.1' connection_id='85234511-...' count=1 data='cba\n' event='echoed data!'
  ... peer='127.0.0.1' connection_id='1c6c0cb5-...' count=4 data='bar\n' event='echoed data!'

Since Twisted's logging system is a bit peculiar, ``structlog`` ships with an :class:`adapter <structlog.twisted.EventAdapter>` so it keeps behaving like you'd expect it to behave.

I'd also like to point out the Counter class that doesn't do anything spectacular but gets bound *once* per connection to the logger and since its repr is the number itself, it's logged out correctly for each event.
This shows off the strength of keeping a dict of objects for context instead of passing around serialized strings.


.. _processors-examples:

Processors
----------

:ref:`Processors` are a both simple and powerful feature of ``structlog``.

So you want timestamps as part of the structure of the log entry, censor passwords, filter out log entries below your log level before they even get rendered, and get your output as JSON for convenient parsing?
Here you go:

.. doctest::

   >>> import datetime, logging, sys
   >>> from structlog import wrap_logger
   >>> from structlog.processors import JSONRenderer
   >>> from structlog.stdlib import filter_by_level
   >>> logging.basicConfig(stream=sys.stdout, format='%(message)s')
   >>> def add_timestamp(_, __, event_dict):
   ...     event_dict['timestamp'] = datetime.datetime.utcnow()
   ...     return event_dict
   >>> def censor_password(_, __, event_dict):
   ...     pw = event_dict.get('password')
   ...     if pw:
   ...         event_dict['password'] = '*CENSORED*'
   ...     return event_dict
   >>> log = wrap_logger(
   ...     logging.getLogger(__name__),
   ...     processors=[
   ...         filter_by_level,
   ...         add_timestamp,
   ...         censor_password,
   ...         JSONRenderer(indent=1, sort_keys=True)
   ...     ]
   ... )
   >>> log.info('something.filtered')
   >>> log.warning('something.not_filtered', password='secret') # doctest: +SKIP
   {
   "event": "something.not_filtered",
   "password": "*CENSORED*",
   "timestamp": "datetime.datetime(..., ..., ..., ..., ...)"
   }

``structlog`` comes with many handy processors build right in -- for a list of shipped processors, check out the :ref:`API documentation <procs>`.
