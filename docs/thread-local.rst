Thread-Local Context
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

   --- David Reid

``structlog`` does its best to have as little global state as possible to achieve its goals.
In an ideal world, you would just stick to its immutable\ [*]_ bound loggers and reap all the rewards of having purely `immutable state <https://en.wikipedia.org/wiki/Immutable_object>`_.

However, we realize that passing loggers around is rather clunky and intrusive in practice.
And since `practicality beats purity <https://www.python.org/dev/peps/pep-0020/>`_, ``structlog`` ships with the `structlog.threadlocal` module to help you to safely have global context storage.

.. [*] In the spirit of Python's 'consenting adults', ``structlog`` doesn't enforce the immutability with technical means.
   However, if you don't meddle with undocumented data, the objects can be safely considered immutable.


The ``merge_threadlocal`` Processor
-----------------------------------

``structlog`` provides a simple set of functions that allow explicitly binding certain fields to a global (thread-local) context and merge them later using a processor into the event dict.

The general flow of using these functions is:

- Use `structlog.configure` with `structlog.threadlocal.merge_threadlocal` as your first processor.
- Call `structlog.threadlocal.clear_threadlocal` at the beginning of your request handler (or whenever you want to reset the thread-local context).
- Call `structlog.threadlocal.bind_threadlocal` as an alternative to your bound logger's ``bind()`` when you want to bind a particular variable to the thread-local context.
- Use ``structlog`` as normal.
  Loggers act as they always do, but the `structlog.threadlocal.merge_threadlocal` processor ensures that any thread-local binds get included in all of your log messages.
- If you want to access the thread-local storage, you use `structlog.threadlocal.get_threadlocal` and `structlog.threadlocal.get_merged_threadlocal`.

.. doctest::

   >>> from structlog.threadlocal import (
   ...     bind_threadlocal,
   ...     clear_threadlocal,
   ...     get_merged_threadlocal,
   ...     get_threadlocal,
   ...     merge_threadlocal,
   ... )
   >>> from structlog import configure
   >>> configure(
   ...     processors=[
   ...         merge_threadlocal,
   ...         structlog.processors.KeyValueRenderer(),
   ...     ]
   ... )
   >>> log = structlog.get_logger()
   >>> # At the top of your request handler (or, ideally, some general
   >>> # middleware), clear the thread-local context and bind some common
   >>> # values:
   >>> clear_threadlocal()
   >>> bind_threadlocal(a=1)
   >>> # Then use loggers as per normal
   >>> # (perhaps by using structlog.get_logger() to create them).
   >>> log.msg("hi")
   a=1 event='hi'
   >>> # You can access the current thread-local state.
   >>> get_threadlocal()
   {'a': 1}
   >>> # Or get it merged with a bound logger.
   >>> get_merged_threadlocal(log.bind(example=True))
   {'a': 1, 'example': True}
   >>> # And when we clear the thread-local state again, it goes away.
   >>> clear_threadlocal()
   >>> log.msg("hi there")
   event='hi there'


Thread-local Contexts
---------------------

``structlog`` also provides thread-local context storage in a form that you may already know from `Flask <https://flask.palletsprojects.com/en/latest/design/#thread-locals>`_ and that makes the *entire context* global to your thread or greenlet.

This makes its behavior more difficult to reason about which is why we generally recommend to use the `merge_threadlocal` route.


Wrapped Dicts
^^^^^^^^^^^^^

In order to make your context thread-local, ``structlog`` ships with a function that can wrap any dict-like class to make it usable for thread-local storage: `structlog.threadlocal.wrap_dict`.

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


To enable thread-local context use the generated class as the context class::

   configure(context_class=WrappedDictClass)

.. note::
   Creation of a new ``BoundLogger`` initializes the logger's context as ``context_class(initial_values)``, and then adds any values passed via ``.bind()``.
   As all instances of a wrapped dict-like class share the same data, in the case above, the new logger's context will contain all previously bound values in addition to the new ones.

`structlog.threadlocal.wrap_dict` returns always a completely *new* wrapped class:

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


In order to be able to bind values temporarily to a logger, `structlog.threadlocal` comes with a `context manager <https://docs.python.org/2/library/stdtypes.html#context-manager-types>`_: `structlog.threadlocal.tmp_bind`\ :

.. testsetup:: ctx

   from structlog import PrintLogger, wrap_logger
   from structlog.threadlocal import tmp_bind, wrap_dict
   WrappedDictClass = wrap_dict(dict)
   log = wrap_logger(PrintLogger(), context_class=WrappedDictClass)

.. doctest:: ctx

   >>> log.bind(x=42)  # doctest: +ELLIPSIS
   <BoundLoggerFilteringAtNotset(context=<WrappedDict-...({'x': 42})>, ...)>
   >>> log.msg("event!")
   x=42 event='event!'
   >>> with tmp_bind(log, x=23, y="foo") as tmp_log:
   ...     tmp_log.msg("another event!")
   x=23 y='foo' event='another event!'
   >>> log.msg("one last event!")
   x=42 event='one last event!'

The state before the ``with`` statement is saved and restored once it's left.

If you want to detach a logger from thread-local data, there's `structlog.threadlocal.as_immutable`.


Downsides & Caveats
~~~~~~~~~~~~~~~~~~~

The convenience of having a thread-local context comes at a price though:

.. warning::
   - If you can't rule out that your application re-uses threads, you *must* remember to **initialize your thread-local context** at the start of each request using :func:`~structlog.BoundLogger.new` (instead of :func:`~structlog.BoundLogger.bind`).
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

     See `configuration` for more details.
   - It `doesn't play well <https://github.com/hynek/structlog/issues/296>`_ with `os.fork` and thus `multiprocessing` (unless configured to use the ``spawn`` start method).

The general sentiment against thread-locals is that they're hard to test.
In this case we feel like this is an acceptable trade-off.
You can easily write deterministic tests using a call-capturing processor if you use the API properly (cf. warning above).

This big red box is also what separates immutable local from mutable global data.
