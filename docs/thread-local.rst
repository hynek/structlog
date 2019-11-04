.. _threadlocal:

Thread Local Context
====================

.. testsetup:: *

   import structlog
   structlog.configure(
       processors=[structlog.processors.KeyValueRenderer()],
   )

.. testcleanup:: *

   import structlog
   structlog.reset_defaults()


Immutability
------------

   You should call some functions with some arguments.

   ---David Reid

The behavior of copying itself, adding new values, and returning the result is useful for applications that keep somehow their own context using classes or closures.
Twisted is a :ref:`fine example <twisted-example>` for that.
Another possible approach is passing wrapped loggers around or log only within your view where you gather errors and events using return codes and exceptions.
If you are willing to do that, you should stick to it because `immutable state <https://en.wikipedia.org/wiki/Immutable_object>`_ is a very good thing\ [*]_.
Sooner or later, global state and mutable data lead to unpleasant surprises.

However, in the case of conventional web development, we realize that passing loggers around seems rather cumbersome, intrusive, and generally against the mainstream culture.
And since it's more important that people actually *use* ``structlog`` than to be pure and snobby, ``structlog`` contains a couple of mechanisms to help here.


The ``merge_threadlocal_context`` Processor
-------------------------------------------

``structlog`` provides a simple set of functions that allow explicitly binding certain fields to a global (thread-local) context.
These functions are :func:`structlog.threadlocal.merge_threadlocal_context`, :func:`structlog.threadlocal.clear_threadlocal`, and :func:`structlog.threadlocal.bind_threadlocal`.

The general flow of using these functions is:

- Use :func:`structlog.configure` with :func:`structlog.threadlocal.merge_threadlocal_context` as your first processor.
- Call :func:`structlog.threadlocal.clear_threadlocal` at the beginning of your request handler (or whenever you want to reset the thread-local context).
- Call :func:`structlog.threadlocal.bind_threadlocal` as an alternative to :func:`structlog.BoundLogger.bind` when you want to bind a particular variable to the thread-local context.
- Use ``structlog`` as normal.
  Loggers act as the always do, but the :func:`structlog.threadlocal.merge_threadlocal_context` processor ensures that any thread-local binds get included in all of your log messages.

.. doctest::

   >>> from structlog.threadlocal import (
   ...     bind_threadlocal,
   ...     clear_threadlocal,
   ...     merge_threadlocal_context,
   ... )
   >>> from structlog import configure
   >>> configure(
   ...     processors=[
   ...         merge_threadlocal_context,
   ...         structlog.processors.KeyValueRenderer(),
   ...     ]
   ... )
   >>> log = structlog.get_logger()
   >>> # At the top of your request handler (or, ideally, some general
   >>> # middleware), clear the threadlocal context and bind some common
   >>> # values:
   >>> clear_threadlocal()
   >>> bind_threadlocal(a=1)
   >>> # Then use loggers as per normal
   >>> # (perhaps by using structlog.get_logger() to create them).
   >>> log.msg("hi")
   a=1 event='hi'
   >>> # And when we clear the threadlocal state again, it goes away.
   >>> clear_threadlocal()
   >>> log.msg("hi there")
   event='hi there'


Thread-local Contexts
---------------------

``structlog`` also provides thread local context storage which you may already know from `Flask <https://flask.palletsprojects.com/en/master/design/#thread-locals>`_:

Thread local storage makes your logger's context global but *only within the current thread*\ [*]_.
In the case of web frameworks this usually means that your context becomes global to the current request.

The following explanations may sound a bit confusing at first but the :ref:`Flask example <flask-example>` illustrates how simple and elegant this works in practice.


Wrapped Dicts
-------------

In order to make your context thread local, ``structlog`` ships with a function that can wrap any dict-like class to make it usable for thread local storage: :func:`structlog.threadlocal.wrap_dict`.

Within one thread, every instance of the returned class will have a *common* instance of the wrapped dict-like class:

.. doctest::

   >>> from structlog.threadlocal import wrap_dict
   >>> WrappedDictClass = wrap_dict(dict)
   >>> d1 = WrappedDictClass({"a": 1})
   >>> d2 = WrappedDictClass({"b": 2})
   >>> d3 = WrappedDictClass()
   >>> d3["c"] = 3
   >>> d1 is d3
   False
   >>> d1 == d2 == d3 == WrappedDictClass()
   True
   >>> d3  # doctest: +ELLIPSIS
   <WrappedDict-...({'a': 1, 'b': 2, 'c': 3})>


To enable thread local context use the generated class as the context class::

   configure(context_class=WrappedDictClass)

.. note::
   Creation of a new ``BoundLogger`` initializes the logger's context as ``context_class(initial_values)``, and then adds any values passed via ``.bind()``.
   As all instances of a wrapped dict-like class share the same data, in the case above, the new logger's context will contain all previously bound values in addition to the new ones.

:func:`structlog.threadlocal.wrap_dict` returns always a completely *new* wrapped class:

.. doctest::

   >>> from structlog.threadlocal import wrap_dict
   >>> WrappedDictClass = wrap_dict(dict)
   >>> AnotherWrappedDictClass = wrap_dict(dict)
   >>> WrappedDictClass() != AnotherWrappedDictClass()
   True
   >>> WrappedDictClass.__name__  # doctest: +SKIP
   WrappedDict-41e8382d-bee5-430e-ad7d-133c844695cc
   >>> AnotherWrappedDictClass.__name__   # doctest: +SKIP
   WrappedDict-e0fc330e-e5eb-42ee-bcec-ffd7bd09ad09


In order to be able to bind values temporarily to a logger, :mod:`structlog.threadlocal` comes with a `context manager <https://docs.python.org/2/library/stdtypes.html#context-manager-types>`_: :func:`~structlog.threadlocal.tmp_bind`\ :

.. testsetup:: ctx

   from structlog import PrintLogger, wrap_logger
   from structlog.threadlocal import tmp_bind, wrap_dict
   WrappedDictClass = wrap_dict(dict)
   log = wrap_logger(PrintLogger(), context_class=WrappedDictClass)

.. doctest:: ctx

   >>> log.bind(x=42)  # doctest: +ELLIPSIS
   <BoundLogger(context=<WrappedDict-...({'x': 42})>, ...)>
   >>> log.msg("event!")
   x=42 event='event!'
   >>> with tmp_bind(log, x=23, y="foo") as tmp_log:
   ...     tmp_log.msg("another event!")
   x=23 y='foo' event='another event!'
   >>> log.msg("one last event!")
   x=42 event='one last event!'

The state before the ``with`` statement is saved and restored once it's left.

If you want to detach a logger from thread local data, there's :func:`structlog.threadlocal.as_immutable`.


Downsides & Caveats
-------------------

The convenience of having a thread local context comes at a price though:

.. warning::
   - If you can't rule out that your application re-uses threads, you *must* remember to **initialize your thread local context** at the start of each request using :func:`~structlog.BoundLogger.new` (instead of :func:`~structlog.BoundLogger.bind`).
     Otherwise you may start a new request with the context still filled with data from the request before.
   - **Don't** stop assigning the results of your ``bind()``\ s and ``new()``\ s!

     **Do**::

      log = log.new(y=23)
      log = log.bind(x=42)

     **Don't**::

      log.new(y=23)
      log.bind(x=42)

     Although the state is saved in a global data structure, you still need the global wrapped logger produce a real bound logger.
     Otherwise each log call will result in an instantiation of a temporary BoundLogger.
     See :ref:`configuration` for more details.

The general sentiment against thread locals is that they're hard to test.
In this case we feel like this is an acceptable trade-off.
You can easily write deterministic tests using a call-capturing processor if you use the API properly (cf. warning above).

This big red box is also what separates immutable local from mutable global data.


.. [*] In the spirit of Python's 'consenting adults', ``structlog`` doesn't enforce the immutability with technical means.
   However, if you don't meddle with undocumented data, the objects can be safely considered immutable.

.. [*] Special care has been taken to detect and support greenlets properly.
