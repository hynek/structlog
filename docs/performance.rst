Performance
===========

``structlog``'s default configuration tries to be as unsurprising and not confusing to new developers as possible.
Some of the choices made come with an avoidable performance price tag -- although its impact is debatable.

Here are a few hints how to get most out of ``structlog`` in production:

#. Use plain `dict`\ s as context classes.
   Python is full of them and they are highly optimized::

      configure(context_class=dict)

   If you don't use automated parsing (you should!) and need predicable order of your keys for some reason, use the `key_order` argument of :class:`~structlog.processors.KeyValueRenderer`.
#. Use a specific wrapper class instead of the generic one.
   ``structlog`` comes with ones for the :doc:`standard-library` and for :doc:`twisted`::

      configure(wrapper_class=structlog.stdlib.BoundLogger)

   :doc:`Writing own wrapper classes <custom-wrappers>` is straightforward too.
#. Avoid (frequently) calling log methods on loggers you get back from :func:`structlog.wrap_logger` and :func:`structlog.get_logger`.
   Since those functions are usually called in module scope and thus before you are able to configure them, they return a proxy that assembles the correct logger on demand.

   Create a local logger if you expect to log frequently without binding::

      logger = structlog.get_logger()
      def f():
         log = logger.bind()
         for i in range(1000000000):
            log.info('iterated', i=i)


#. Set the `cache_logger_on_first_use` option to `True` so the aforementioned on-demand loggers will be assembled only once and cached for future uses::

      configure(cache_logger_on_first_use=True)

   This has the only drawback is that later calls on :func:`~structlog.configure` don't have any effect on already cached loggers -- that shouldn't matter outside of testing though.
#. Use a faster JSON serializer than the standard library.
   Possible alternatives are among others simplejson_, UltraJSON_, or RapidJSON_ (Python 3 only)::

      structlog.processors.JSONRenderer(serializer=rapidjson.dumps)


.. _simplejson: https://simplejson.readthedocs.io/
.. _UltraJSON: https://github.com/esnme/ultrajson/
.. _RapidJSON: https://pypi.python.org/pypi/python-rapidjson/
