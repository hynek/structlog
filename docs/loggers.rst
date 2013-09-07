Loggers
=======

The center of structlog is the immutable log wrapper :class:`~structlog.BoundLogger`.

All it does is:

- Keeping a *context* and a *logger* it's wrapping,
- recreating itself with (optional) additional context data (the :func:`~structlog..BoundLogger.bind` and :func:`~structlog.BoundLogger.new` methods),
- and finally relaying *all* other method calls to the wrapped logger after processing the log entry with the configured chain of processors.

You won't be instantiating it yourself though.
For that there is the :func:`structlog.wrap_logger` function:

.. literalinclude:: code_examples/loggers/simplest.txt
   :language: pycon

As you can see, it accepts one mandatory and two optional arguments:

**logger**
   Only positional argument is the logger that you want to wrap and to which the log entries will be proxied.
   Since a wrapped logger without a logger doesn't make any sense, this argument is *mandatory*.

**processors**
   A list of callables that can :ref:`filter, mutate, and format <processors>` the log entry before it gets passed to the wrapped logger.

   Default is ``[``:func:`~structlog.processors.format_exc_info`, :class:`~structlog.processors.KeyValueRenderer`\ ``]``.

**context_class**
   The class to save your context in.
   Particularly useful for :ref:`thread local context storage <threadlocal>`.

   Default is OrderedDict_.

This example also demonstrates how structlog is *not* dependent on Python's standard library logging module.

.. note::

   Free your mind from the preconception that log entries have to be serialized to strings eventually.
   All structlog cares about is a *dictionary* of *keys* and *values*.
   What happens to it depends on the logger you wrap and your processors alone.

   This gives you the power to log directly to databases, log aggregation servers, web services, and whatnot.


Convenience Helpers
-------------------

To make the most common cases more convenient, there are helper functions for stdlib and Twisted:

- :func:`structlog.stdlib.get_logger`
- :func:`structlog.twisted.get_logger`

For even more convenience and accessibility, structlog *ships* with the class :class:`~structlog.PrintLogger` because it's handy for both examples and in combination with tools like `runit <http://smarden.org/runit/>`_ or `stdout/stderr-forwarding <http://hynek.me/articles/taking-some-pain-out-of-python-logging/>`_.

Additionally -- but arguably mostly for my own unit testing convenience -- structlog also ships with a logger that just returns whatever it gets passed into it: :class:`~structlog.ReturnLogger`.

.. literalinclude:: code_examples/loggers/return_logger.txt
   :language: pycon

.. _configuration:

Configuration
-------------

structlog allows you to set global default values for both ``processors`` and ``context_class`` so ideally your logging boilerplate in regular application consists only of::

   from structlog.stdlib import get_logger
   logger = get_logger()

or::

   from structlog import BoundLogger
   logger = BoundLogger.wrap(YourLogger())

if you don't use a directly supported logger.

To achieve that you'll have to call :func:`structlog.configure` on app initialization (if you're not content with the defaults that is).
The previous example could thus have been written as following:

.. literalinclude:: code_examples/loggers/simplest_configure.txt
   :language: pycon
   :emphasize-lines: 8-9
   :start-after: return repr(event_dict)
   :end-before: reset_defaults

structlog tries to behave in the least surprising way when it comes to handling defaults and configuration:

#. Passed `processors` and `context_class` arguments to :func:`structlog.wrap_logger` *always* take the highest precedence.
   That means that you can overwrite whatever you've configured for each logger respectively.
#. If you leave them on `None`, structlog will check whether you've configured default values using :func:`structlog.configure` and uses them if so.

   Since you will call :func:`structlog.wrap_logger` (or one of the ``get_logger()`` functions)  most likely at import time and thus before you had a chance to configure structlog, they all return a proxy that returns a correct BoundLogger on first ``bind()``/``new()``.

   To enable you to log with the module-global logger, it will create a temporary BoundLogger and relay the log calls to it on *each call*.
   Therefore if you have nothing to bind but intend to do lots of log calls in a function, it makes sense performance-wise to create a local logger by calling ``bind()`` or ``new()`` without any parameters.

#. If you haven't configured or passed anything at all, the default fallback values are used which means OrderedDict_ for context and ``[``:func:`~structlog.processors.format_exc_info`, :class:`~structlog.processors.KeyValueRenderer`\ ``]`` for the processor chain.

If necessary, you can always reset your global configuration back to default values using :func:`structlog.reset_defaults`.
That can be handy in tests.


Where to Configure
^^^^^^^^^^^^^^^^^^

The best place to perform your configuration varies with applications and frameworks:

**Django**
   Django has to date unfortunately no concept of an application assembler or "app is done" hooks.
   Therefore the bottom of your ``settings.py`` will have to do.

**Flask**
   TBD

**Pyramid**
   `Application constructor <http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/startup.html#the-startup-process>`_.

**Twisted**
   The `plugin definition <http://twistedmatrix.com/documents/current/core/howto/plugin.html>`_ is the best place.
   If your app is not a plugin, put it into your `tac file <http://twistedmatrix.com/documents/current/core/howto/application.html>`_ (and then `learn <https://bitbucket.org/jerub/twisted-plugin-example>`_ about plugins).

If you have no choice but *have* to configure on import time in module-global scope, or can't rule out for other reasons that that your :func:`structlog.configure` gets called more than once, structlog offers :func:`structlog.configure_once` that does nothing if structlog has been configured before (no matter whether using :func:`structlog.configure` or :func:`~structlog.configure_once`).


Immutability
------------

   You should call some functions with some arguments.

   ---David Reid

The behavior of copying itself, adding new values, and returning the result is useful for applications that keep somehow their own context using classes or closures.
Twisted is a :ref:`fine example <twisted-example>` for that.
Another possible approach is passing wrapped loggers around or log only within your view where you gather errors and events using return codes and exceptions.
If you are willing to do that, you should stick to it because `immutable state <http://en.wikipedia.org/wiki/Immutable_object>`_ is a very good thing\ [*]_.
Sooner or later, global state and mutable data lead to unpleasant surprises.

However, in the case of conventional web development, I realize that passing loggers around seems rather cumbersome, intrusive, and generally against the mainstream culture.
And since it's more important that people actually *use* structlog than to be pure and snobby, structlog contains a dirty but convenient trick: thread local context storage which you may already know from `Flask <http://flask.pocoo.org/docs/design/#thread-locals>`_.


.. [*] In the spirit of Python's 'consenting adults', structlog doesn't enforce the immutability with technical means.
   However, if you don't meddle with undocumented data, the objects can be safely considered immutable.


.. _threadlocal:

Thread Local Context
--------------------

Thread local storage makes your logger's context global but *only within the current thread*\ [*]_.
In the case of web frameworks this usually means that your context becomes global to the current request.

The following explanations may sound a bit confusing at first but the :ref:`Flask example <flask-example>` illustrates how simple and elegant this works in practice.


Wrapped Dicts
^^^^^^^^^^^^^

In order to make your context thread local, structlog ships with a function that can wrap any dict-like class to make it usable for thread local storage: :func:`structlog.threadlocal.wrap_dict`.

Within one thread, every instance of the returned class will have a *common* instance of the wrapped dict-like class:

.. literalinclude:: code_examples/loggers/thread_local_dicts.txt
   :language: pycon

Then use an instance of the generated class as the context class::

   configure(context_class=WrappedDictClass())

.. note::
   **Remember**: the instance of the class *doesn't* matter.
   Only the class *type* matters because *all* instances of one class *share* the *same* data.

:func:`structlog.threadlocal.wrap_dict` returns always a completely *new* wrapped class:

.. literalinclude:: code_examples/loggers/thread_local_classes.txt
   :language: pycon
   :start-after: wrap_dict(dict)

In order to be able to bind values temporarily to a logger, :mod:`structlog.threadlocal` comes with a `context manager <http://docs.python.org/2/library/stdtypes.html#context-manager-types>`_: :func:`~structlog.threadlocal.tmp_bind`\ :

.. literalinclude:: code_examples/loggers/thread_local_context_manager.txt
   :language: pycon
   :start-after: context_class=WrappedDictClass)


Downsides & Caveats
^^^^^^^^^^^^^^^^^^^

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
     ee :ref:`configuration` for more details.

The general sentiment against thread locals is that they're hard to test.
In this case I feel like this is an acceptable trade-off.
You can easily write deterministic tests using a call-capturing processor if you use the API properly (cf. warning above).

This big red box is also what separates immutable local from mutable global data.


.. [*] Gevent's monkeypatching `automatically <http://www.gevent.org/gevent.monkey.html>`_ adapts thread local storage to greenlet local storage.


.. _OrderedDict: http://docs.python.org/2/library/collections.html#collections.OrderedDict
