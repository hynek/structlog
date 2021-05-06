Performance
===========

``structlog``'s default configuration tries to be as unsurprising to new developers as possible.
Some of the choices made come with an avoidable performance price tag -- although its impact is debatable.

Here are a few hints how to get most out of ``structlog`` in production:

#. Use a specific wrapper class instead of the generic one.
   ``structlog`` comes with ones for the :doc:`standard-library` and for :doc:`twisted`::

      configure(wrapper_class=structlog.stdlib.BoundLogger)

   ``structlog`` also comes with native log levels that are based on the ones from the standard library (read: we've copy and pasted them), but don't involve `logging`'s dynamic machinery.
   That makes them *much* faster.
   You can use `structlog.make_filtering_bound_logger()` to create one.

   :doc:`Writing own wrapper classes <custom-wrappers>` is straightforward too.

#. Avoid (frequently) calling log methods on loggers you get back from :func:`structlog.wrap_logger` and :func:`structlog.get_logger`.
   Since those functions are usually called in module scope and thus before you are able to configure them, they return a proxy that assembles the correct logger on demand.

   Create a local logger if you expect to log frequently without binding::

      logger = structlog.get_logger()
      def f():
         log = logger.bind()
         for i in range(1000000000):
            log.info("iterated", i=i)


#. Set the *cache_logger_on_first_use* option to `True` so the aforementioned on-demand loggers will be assembled only once and cached for future uses::

      configure(cache_logger_on_first_use=True)

   This has two drawbacks:

   1. Later calls of :func:`~structlog.configure` don't have any effect on already cached loggers -- that shouldn't matter outside of :doc:`testing <testing>` though.
   2. The resulting bound logger is not pickleable.
      Therefore, you can't set this option if you e.g. plan on passing loggers around using `multiprocessing`.

#. Avoid sending your log entries through the standard library if you can: its dynamic nature and flexibiliy make it a major bottleneck.
   Instead use `structlog.PrintLoggerFactory` or -- if your serializer returns bytes (e.g. orjson_) -- `structlog.BytesLoggerFactory`.

   You can still configure `logging` for packages that you don't control, but avoid it for your *own* log entries.

#. Use a faster JSON serializer than the standard library.
   Possible alternatives are among others are orjson_ or RapidJSON_.


Example
-------


Here's an example for a production-ready non-asyncio ``structlog`` configuration that's as fast as it gets::

  import logging
  import structlog

  structlog.configure(
      cache_logger_on_first_use=True,
      wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
      processors=[
          structlog.threadlocal.merge_threadlocal_context,
          structlog.processors.add_log_level,
          structlog.processors.format_exc_info,
          structlog.processors.TimeStamper(fmt="iso", utc=False),
          structlog.processors.JSONRenderer(serializer=orjson.dumps),
      ],
      logger_factory=structlog.BytesLoggerFactory(),
  )

It has the following properties:

- Caches all loggers on first use.
- Filters all log entries below the ``info`` log level **very** efficiently.
  The ``debug`` method literally consists of ``return None``.
- Supports `thread-local`.
- Adds the log level name.
- Renders exceptions.
- Adds an `ISO 8601 <https://en.wikipedia.org/wiki/ISO_8601>`_ timestamp under the ``timestamp`` key in the UTC timezone.
- Renders the log entries as JSON using orjson_ which is faster than plain logging in `logging`.
- Uses `BytesLoggerFactory` because orjson returns bytes.
  That saves encoding ping-pong.

Therefore a log entry might look like this:

.. code:: json

   {"event":"hello","timestamp":"2020-11-17T09:54:11.900066Z"}

----

If you need standard library support for external projects, you can either just use a JSON formatter like `python-json-logger <https://pypi.org/project/python-json-logger/>`_, or pipe them through ``structlog`` as documented in `standard-library`.


.. _simplejson: https://simplejson.readthedocs.io/
.. _orjson: https://github.com/ijl/orjson
.. _RapidJSON: https://pypi.org/project/python-rapidjson/
