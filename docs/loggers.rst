Loggers
=======

The center of structlog is the immutable log wrapper :class:`structlog.loggers.BoundLogger`.

In it's core, all it does is:

- wrapping an *arbitrary* logging class (:func:`structlog.loggers.BoundLogger.wrap`),
- recreating itself with (optional) additional context data (:func:`structlog.loggers.BoundLogger.bind` and :func:`structlog.loggers.BoundLogger.new`),
- configuring global default values for the processor chain and the class used to keep the context (:func:`structlog.loggers.BoundLogger.configure`),
- and finally relaying *all* other method calls to the wrapped logger after processing the log entry with the configured chain of processors.

.. literalinclude:: code_examples/loggers/simplest.txt
   :language: pycon

This example also demonstrates how structlog is *not* dependent on Python's standard library logging module.
It can wrap *anything*.
Really.
*No* depedency on stdlib logging *whatsoever*.
*Yes*, you can use your own logger underneath.

To make the most common cases more convenient, there are helper functions for stdlib and Twisted though:

- :func:`structlog.stdlib.get_logger`
- :func:`structlog.twisted.get_logger`


.. _configuration:

Configuration
-------------

structlog allows you to set global default values for both ``processors`` and ``context_class`` so ideally your logging boilerplate in regular application consists only of::

   from structlog.stdlib import get_logger
   logger = get_logger()

or::

   from structlog import BoundLogger
   logger = BoundLogger.wrap(PrintLogger())

if you don't use a directly supported logger.

To achieve that you'll have to call :func:`structlog.loggers.BoundLogger.configure` on app initialization (if you're not content with the -- hopefully -- sane defaults that is).
The previous example could thus have been written as following:

.. literalinclude:: code_examples/loggers/simplest_configure.txt
   :language: pycon
   :emphasize-lines: 8-9
   :start-after: return repr(event_dict)
   :end-before: reset_defaults

structlog tries to behave in the least surprising way when it comes to handling defaults and configuration:

#. Passed `processors` and `context_class` arguments to :func:`structlog.loggers.BoundLogger.wrap` *always* take the highest precedence.
   That means that you can overwrite whatever you've configured for each logger respectively.
#. If you leave them on `None`, structlog will check whether you've configured default values using :func:`structlog.loggers.BoundLogger.configure` and uses them if so.

   Precautions are taken to convert the context class if it changes between bindings.
   This is important because your level logger is likely to be created in global scope at import time; i.e. before you had the chance to configure your defaults.
#. If you haven't configured or passed anything at all, the default fallback values are used which means ``OrderedDict`` for context and :func:`structlog.processors.format_exc_info` and :class:`structlog.processors.KeyValueRenderer` for the processor chain.

If necessary, you can always reset your global configuration back to default values using :func:`structlog.loggers.BoundLogger.reset_defaults`.
That can be handy in tests.

The best place to perform your configuration varies with applications and frameworks:

**Django**
   Django has to date unfortunately no concept of an application assembler or "app is done" hooks.
   Therefore the bottom of your ``settings.py`` will have to do.

**Flask**
   WIP

**Pyramid**
   `Application constructor <http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/startup.html#the-startup-process>`_.

**Tornado**
   WIP

**Twisted**
   The `plugin definition <http://twistedmatrix.com/documents/current/core/howto/plugin.html>`_ is the best place.
   If your app is not a plugin, put it into your `tac file <http://twistedmatrix.com/documents/current/core/howto/application.html>`_ (and then `learn <https://bitbucket.org/jerub/twisted-plugin-example>`_ about plugins).

If you have no choice but *have* to configure on import time in global scope, or can't rule out for other reasons that that your `configure()` gets called more than once, structlog offers :func:`structlog.loggers.BoundLogger.configure_once` that does nothing if structlog has been configured before (no matter whether using `configure()` or `configure_once()`).

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


.. _threadlocal:

Thread Local Context
--------------------

Thread local storage makes your logger's context global but local to the current thread\ [*]_.
In the case of web frameworks this means that your context becomes global to the current request.

In order to make your context thread local, structlog ships with a function that can wrap any dict-like class to make it usable for thread local storage: :func:`structlog.threadlocal.wrap_dict`.

Within one thread, every instance of the returned class will have a *common* instance of the wrapped dict-like class:

.. literalinclude:: code_examples/loggers/thread_local_dicts.txt
   :language: pycon

Then use an instance of the generated class as the context class::

   BoundLogger.configure(context_class=WrappedDictClass())

Remember: the instance of the class is irrelevant, only the class *type* matters because all instances of one class share the same data.

:func:`structlog.threadlocal.wrap_dict` returns always a completely *new* wrapped class:

.. literalinclude:: code_examples/loggers/thread_local_classes.txt
   :language: pycon
   :start-after: wrap_dict(dict)

The convenience of having a thread local context comes at a price though:

.. warning::
   If you can't rule out that your application re-uses threads, you have have to remember to re-initialize your thread local context at the start of each request using ``new()`` (instead of ``bind()``) so you don't start a new request with the context still filled with data from the last one.

This all may sound a bit confusing at first but the :ref:`Flask example <flask-example>` illustrates how simple and elegant this works in practice.

The general sentiment against thread locals is that they're hard to test.
In this case I feel like this is an acceptable trade-off.
You can easily write deterministic tests using a call-capturing processor if you use the API properly (cf. warning above).


.. [*] Please note that in Python's 'consenting adults spirit', structlog does *not* enforce the immutability with technical means.
   However, if you don't meddle with undocumented data, the objects can be safely considered immutable.

.. [*] Gevent's monkeypatching `automatically <http://www.gevent.org/gevent.monkey.html>`_ adapts thread local storage to greenlet local storage.
