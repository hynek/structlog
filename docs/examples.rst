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


.. _twisted-example:

Twisted
-------

If you prefer to log less but with more context in each entry, you can bind everything important to your logger and log it out with each log entry.


.. literalinclude:: code_examples/twisted_echo.py
   :language: python

Since Twisted's logging system is a big peculiar, structlog ships with an adapter (:class:`structlog.twisted.LogAdapter`) so it keeps behaving like you'd expect it to behave.


Processors
----------

So you want timestamps as part of the structure of the log entry, censor passwords, filter out log entries below your log level before they even get rendered, and get your output as JSON for convenient parsing?
Here you go:

.. literalinclude:: code_examples/processors.txt
   :language: pycon

structlog comes with many handy processors build right in – check them out in the :ref:`API <API>` documentation!

Of course you can set default processors and context classes once globally.
