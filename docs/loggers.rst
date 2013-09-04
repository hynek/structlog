Loggers
=======

The center of structlog is the immutable log wrapper :class:`structlog.loggers.BoundLogger`.
In it's core, it just allows you to wrap an *arbitrary* logging class (:func:`structlog.loggers.BoundLogger.wrap` class method) to recreate itself with added data to the current context (:func:`structlog.loggers.BoundLogger.bind` and :func:`structlog.loggers.BoundLogger.new` methods) and relay log calls to the wrapped logger after processing the log entry with a chain of processors.

.. literalinclude:: code_examples/loggers/simplest.txt
   :language: pycon

This example also demonstrates how structlog is *not* dependent on Python’s or Twisted’s logging.
It can wrap *anything*.
Really.
*No* depedency on stdlib logging *whatsoever*.

Immutability
------------

This behavior by itself is already very useful for single-threaded applications that keep somehow their own context using classes or closures.
Twisted is a :ref:`fine example <twisted-example>`.
If you can, you should stick to it because `immutable state <http://en.wikipedia.org/wiki/Immutable_object>`_ is a very good thing\ [*]_.

However, in the case of web frameworks, the handing around of loggers to every function and method seems rather inconvenient.
Hence structlog contains a slightly dirty but convenient trick: thread local context storage.

Thread Local Context
--------------------

Additionally to the processor chain, BoundLogger's ``wrap`` class method offers a second argument: the dict-like class that is used for storing the context dictionary.
By default, OrderedDict is used to keep you log data approximately in the same order as you put it in.

In order to make your context thread local (that is: global, but only within your thread; in web frameworks this usually means within one request), structlog ships with a generic wrapper for dict-like classes called :class:`structlog.threadlocal.ThreadLocalDict`.

.. warning::

   You have have to remember to re-initialize your thread local context at the start of each request using ``new()`` (instead of ``bind()``).

   So in case your application container reuses threads you don't start a new request with the context still filled with the last one.

Have a look at the :ref:`Flask example <flask-example>` how this works in practice.

.. [*] Please note that in Python's 'consenting adults spirit', structlog does *not* enforce the immutability with technical means.
   However, if you don't meddle with undocumented data, the objects can be safely considered immutable.
