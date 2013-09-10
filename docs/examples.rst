.. _examples:

Examples
========

This chapter is intended to give you a taste of realistic usage of structlog.


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

Please note that :class:`structlog.stdlib.LoggerFactory` is a totally magic-free class that just deduces the name of the caller's module and does a `logging.getLogger() <http://docs.python.org/2/library/logging.html#logging.getLogger>`_. with it.
It's used by :func:`struclog.get_logger` to rid you of logging boilerplate in application code.


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
  ... peer='127.0.0.1' connection_id='1c6c0cb5-...' count=4 data='bar\n' event='echoed data!' 

Since Twisted's logging system is a bit peculiar, structlog ships with an :class:`adapter <structlog.twisted.EventAdapter>` so it keeps behaving like you'd expect it to behave.

I'd also like to point out the Counter class that doesn't do anything spectacular but gets bound *once* per connection to the logger and since its repr is the number itself, it's logged out correctly for each event.
This shows off the strength of keeping a dict of objects for context instead of passing around serialized strings.

.. _processors-examples:

Processors
----------

:ref:`Processors` are a both simple and powerful feature of structlog.

So you want timestamps as part of the structure of the log entry, censor passwords, filter out log entries below your log level before they even get rendered, and get your output as JSON for convenient parsing?
Here you go:

.. literalinclude:: code_examples/processors.txt
   :language: pycon

structlog comes with many handy processors build right in -- for a list of shipped processors, check out the :ref:`API documentation <procs>`.


.. _wrapper_class-example:

Custom Wrapper Classes
----------------------

A custom wrapper class helps you to cast the shackles of your underlying logging system even further and get rid of even more boilerplate.

.. literalinclude:: code_examples/custom_wrapper.txt
   :language: pycon

I like to have semantically meaningful logger names.
If you agree, this is a nice way to achieve that.


Of course, you can :ref:`configure <configuration>` default processors, the wrapper class and the context classes globally.
