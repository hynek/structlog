Examples
========

This chapter is intended to give you a taste of realistic usage of ``structlog``.


.. _flask-example:

Flask and Thread-Local Data
---------------------------

Let's assume you want to bind a unique request ID, the URL path, and the peer's IP to every log entry by storing it in thread-local storage that is managed by context variables:

.. literalinclude:: code_examples/flask_/webapp.py
   :language: python

``some_module.py``

.. literalinclude:: code_examples/flask_/some_module.py
   :language: python

This would result among other the following lines to be printed:

.. code:: text

   event='user logged in' view='/login' peer='127.0.0.1' user='test-user' request_id='e08ddf0d-23a5-47ce-b20e-73ab8877d736'
   event='user did something' view='/login' peer='127.0.0.1' something='shot_in_foot' request_id='e08ddf0d-23a5-47ce-b20e-73ab8877d736'

As you can see, ``view``, ``peer``, and ``request_id`` are present in **both** log entries.

While wrapped loggers are *immutable* by default, this example demonstrates how to circumvent that using a thread-local storage for request-wide context:

1. `structlog.contextvars.clear_contextvars()` ensures the thread-local storage is empty for each request.
2. `structlog.contextvars.bind_contextvars()` puts your key-value pairs into thread-local storage.
3. The `structlog.contextvars.merge_contextvars()` processor merges the thread-local context into the event dict.

Please note that the ``user`` field is only present in the view because it wasn't bound into the thread-local storage.
See :doc:`contextvars` for more details.

----

`structlog.stdlib.LoggerFactory` is a totally magic-free class that just deduces the name of the caller's module and does a `logging.getLogger` with it.
It's used by `structlog.get_logger` to rid you of logging boilerplate in application code.
If you prefer to name your standard library loggers explicitly, a positional argument to `structlog.get_logger` gets passed to the factory and used as the name.


.. _processors-examples:

Processors
----------

:doc:`processors` are a both simple and powerful feature of ``structlog``.

The following example demonstrates how easy it is to add timestamps, censor passwords, filter out log entries below your log level before they even get rendered, and get your output as JSON for convenient parsing.
It also demonstrates how to use `structlog.wrap_logger` that allows you to use ``structlog`` without any global configuration (a rather uncommon pattern, but can be useful):

.. doctest::

   >>> import datetime, logging, sys
   >>> from structlog import wrap_logger
   >>> from structlog.processors import JSONRenderer
   >>> from structlog.stdlib import filter_by_level
   >>> logging.basicConfig(stream=sys.stdout, format="%(message)s")
   >>> def add_timestamp(_, __, event_dict):
   ...     event_dict["timestamp"] = datetime.datetime.utcnow()
   ...     return event_dict
   >>> def censor_password(_, __, event_dict):
   ...     pw = event_dict.get("password")
   ...     if pw:
   ...         event_dict["password"] = "*CENSORED*"
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
   >>> log.info("something.filtered")
   >>> log.warning("something.not_filtered", password="secret") # doctest: +ELLIPSIS
   {
    "event": "something.not_filtered",
    "password": "*CENSORED*",
    "timestamp": "datetime.datetime(..., ..., ..., ..., ...)"
   }

``structlog`` comes with many handy processors build right in, so check the :ref:`API documentation <procs>` before you write your own.
For example, you probably don't want to write your own timestamper.


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
