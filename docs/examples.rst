.. _examples:

Examples
========

This chapter is intended to give you a taste of realistic usage of structlog.


.. _flask-example:

Flask
-----

In the simplest case, you bind a unique request ID to every incoming request so you can easily see which log entries belong to which request.

.. literalinclude:: code_examples/flask_/webapp.py
   :language: python

``some_module.py``

.. literalinclude:: code_examples/flask_/some_module.py
   :language: python

While wrapped loggers are *immutable* by default, this example demonstrates how to circumvent that using a thread local dict implementation for context data for convenience (hence the requirement for using `new()` for re-initializing the logger).

Please note that :func:`structlog.stdlib.get_logger` is a totally magic-free convenience function that just deduces the name of the caller's module and calls :func:`structlog.loggers.BoundLogger.wrap()` on `logging.getLogger() <http://docs.python.org/2/library/logging.html#logging.getLogger>`_.


.. _twisted-example:

Twisted
-------

If you prefer to log less but with more context in each entry, you can bind everything important to your logger and log it out with each log entry.


.. literalinclude:: code_examples/twisted_echo.py
   :language: python

Since Twisted's logging system is a bit peculiar, structlog ships with an adapter (:class:`structlog.twisted.LogAdapter`) so it keeps behaving like you'd expect it to behave.

Again, :func:`structlog.twisted.get_logger` is just a thin and simple convenience wrapper.


.. _processors-examples:

Processors
----------

:ref:`Processors` are a both simple and powerful feature of structlog.

So you want timestamps as part of the structure of the log entry, censor passwords, filter out log entries below your log level before they even get rendered, and get your output as JSON for convenient parsing?
Here you go:

.. literalinclude:: code_examples/processors.txt
   :language: pycon

structlog comes with many handy processors build right in -- check them out in the :mod:`API <structlog.processors>` documentation to learn more!

Of course you can :ref:`configure <configuration>` default processors and context classes globally.
