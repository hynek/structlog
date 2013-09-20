Loggers
=======

.. testcleanup:: *

   import structlog
   structlog.reset_defaults()

The center of structlog is the immutable log wrapper :class:`~structlog.BoundLogger`.

All it does is:

- Keeping a *context dictionary* and a *logger* that it's wrapping,
- recreating itself with (optional) *additional* context data (the :func:`~structlog.BoundLogger.bind` and :func:`~structlog.BoundLogger.new` methods),
- recreating itself with *less* data (:func:`~structlog.BoundLogger.unbind`),
- and finally relaying *all* other method calls to the wrapped logger after processing the log entry with the configured chain of :ref:`processors <processors>`.

You won't be instantiating it yourself though.
For that there is the :func:`structlog.wrap_logger` function (or the convenience function :func:`structlog.get_logger` we'll discuss in a minute):

.. doctest::

   >>> from structlog import wrap_logger
   >>> class PrintLogger(object):
   ...     def msg(self, message):
   ...         print message
   >>> def proc(logger, method_name, event_dict):
   ...     print 'I got called with', event_dict
   ...     return repr(event_dict)
   >>> log = wrap_logger(PrintLogger(), processors=[proc], context_class=dict)
   >>> log2 = log.bind(x=42)
   >>> log == log2
   False
   >>> log.msg('hello world')
   I got called with {'event': 'hello world'}
   {'event': 'hello world'}
   >>> log2.msg('hello world')
   I got called with {'x': 42, 'event': 'hello world'}
   {'x': 42, 'event': 'hello world'}
   >>> log3 = log2.unbind('x')
   >>> log == log3
   True
   >>> log3.msg('nothing bound anymore', foo='but you can structure the event too')
   I got called with {'foo': 'but you can structure the event too', 'event': 'nothing bound anymore'}
   {'foo': 'but you can structure the event too', 'event': 'nothing bound anymore'}

As you can see, it accepts one mandatory and a few optional arguments:

**logger**
   The one an only positional argument is the logger that you want to wrap and to which the log entries will be proxied.
   If you wish to use a :ref:`configured logger factory <logger-factories>`, set it to `None`.

**processors**
   A list of callables that can :ref:`filter, mutate, and format <processors>` the log entry before it gets passed to the wrapped logger.

   Default is ``[``:func:`~structlog.processors.format_exc_info`, :class:`~structlog.processors.KeyValueRenderer`\ ``]``.

**context_class**
   The class to save your context in.
   Particularly useful for :ref:`thread local context storage <threadlocal>`.

   Default is OrderedDict_.

Additionally, the following arguments are allowed too:

**wrapper_class**
   A class to use instead of :class:`~structlog.BoundLogger` for wrapping.
   This is useful if you want to sub-class BoundLogger and add custom logging methods.
   BoundLogger's bind/new methods are sub-classing friendly so you won't have to re-implement them.
   Please refer to the :ref:`related example <wrapper_class-example>` how this may look like.

**initial_values**
   The values that new wrapped loggers are automatically constructed with.
   Useful for example if you want to have the module name as part of the context.

.. note::

   Free your mind from the preconception that log entries have to be serialized to strings eventually.
   All structlog cares about is a *dictionary* of *keys* and *values*.
   What happens to it depends on the logger you wrap and your processors alone.

   This gives you the power to log directly to databases, log aggregation servers, web services, and whatnot.


Shipped Loggers
---------------

To save you the hassle of using standard library logging for simple stdout logging, structlog ships a :class:`~structlog.PrintLogger`.
It's handy for both examples and in combination with tools like `runit <http://smarden.org/runit/>`_ or `stdout/stderr-forwarding <http://hynek.me/articles/taking-some-pain-out-of-python-logging/>`_.

Additionally -- mostly for unit testing -- structlog also ships with a logger that just returns whatever it gets passed into it: :class:`~structlog.ReturnLogger`.

.. doctest::

   >>> from structlog import ReturnLogger
   >>> ReturnLogger().msg(42) == 42
   True
   >>> obj = ['hi']
   >>> ReturnLogger().msg(obj) is obj
   True


.. _configuration:

Configuration
-------------

To make logging as unintrusive and straight-forward to use as possible, structlog comes with a plethora of configuration options and convenience functions.
Let me start at the end and introduce you to the ultimate convenience function that relies purely on configuration: :func:`structlog.get_logger` (and its Twisted-friendly alias :func:`structlog.getLogger`).

The goal is to reduce your per-file logging boilerplate to::

   from structlog.stdlib import get_logger
   logger = get_logger()

while still giving you the full power via configuration.

To achieve that you'll have to call :func:`structlog.configure` on app initialization (of course, only if you're not content with the defaults).
The previous example could thus have been written as following:

.. testsetup:: config

   from structlog import PrintLogger, configure, reset_defaults, wrap_logger, get_logger
   from structlog.threadlocal import wrap_dict
   def proc(logger, method_name, event_dict):
      print 'I got called with', event_dict
      return repr(event_dict)

.. doctest:: config

   >>> configure(processors=[proc], context_class=dict)
   >>> log = wrap_logger(PrintLogger())
   >>> log.msg('hello world')
   I got called with {'event': 'hello world'}
   {'event': 'hello world'}


In fact, it could even be written like

.. doctest:: config

   >>> configure(processors=[proc], context_class=dict)
   >>> log = get_logger()
   >>> log.msg('hello world')
   I got called with {'event': 'hello world'}
   {'event': 'hello world'}

because :class:`~structlog.processors.PrintLogger` is the default LoggerFactory used (see :ref:`logger-factories`).

structlog tries to behave in the least surprising way when it comes to handling defaults and configuration:

#. Passed `processors`, `wrapper_class`, and `context_class` arguments to :func:`structlog.wrap_logger` *always* take the highest precedence.
   That means that you can overwrite whatever you've configured for each logger respectively.
#. If you leave them on `None`, structlog will check whether you've configured default values using :func:`structlog.configure` and uses them if so.
#. If you haven't configured or passed anything at all, the default fallback values are used which means OrderedDict_ for context and ``[``:func:`~structlog.processors.format_exc_info`, :class:`~structlog.processors.KeyValueRenderer`\ ``]`` for the processor chain.

If necessary, you can always reset your global configuration back to default values using :func:`structlog.reset_defaults`.
That can be handy in tests.

.. note::

   Since you will call :func:`structlog.wrap_logger` (or one of the ``get_logger()`` functions) most likely at import time and thus before you had a chance to configure structlog, they return a **proxy** that returns a correct wrapped logger on first ``bind()``/``new()``.

   Therefore, you must not call ``new()`` or ``bind()`` in module scope!
   Use :func:`~structlog.get_logger`\ 's ``initial_values`` to achieve pre-populated contexts.

   To enable you to log with the module-global logger, it will create a temporary BoundLogger and relay the log calls to it on *each call*.
   Therefore if you have nothing to bind but intend to do lots of log calls in a function, it makes sense performance-wise to create a local logger by calling ``bind()`` or ``new()`` without any parameters.


.. _logger-factories:

Logger Factories
^^^^^^^^^^^^^^^^

To make :func:`structlog.get_logger` work, one needs one more option that hasn't been discussed yet: ``logger_factory``.

It is a callable that returns the logger that gets wrapped and returned.
In the simplest case, it's a function that returns a logger -- or just a class.
But you can also pass in an instance of a class with a ``__call__`` method for more complicated setups.

For the common cases of standard library logging and Twisted logging, structlog comes with two factories built right in:

- :class:`structlog.stdlib.LoggerFactory`
- :class:`structlog.twisted.LoggerFactory`

So all it takes to use structlog with standard library logging is this::

   >>> from structlog import get_logger, configure
   >>> from structlog.stdlib import LoggerFactory
   >>> configure(logger_factory=LoggerFactory())
   >>> log = get_logger()
   >>> log.critical('this is too easy!')
   event='this is too easy!'

The :ref:`Twisted example <twisted-example>` shows how easy it is for Twisted.

.. note::

   `LoggerFactory()`-style factories always need to get passed as *instances* like in the examples above.
   While neither allows for customization using parameters yet, they may do so in the future.

Calling :func:`structlog.get_logger` without configuration gives you a perfectly useful :class:`structlog.PrintLogger` with the default values exaplained above.
I don't believe silent loggers are a sensible default.


Where to Configure
^^^^^^^^^^^^^^^^^^

The best place to perform your configuration varies with applications and frameworks.
Ideally as late as possible but *before* non-framework (i.e. your) code is executed.
If you use standard library's logging, it makes sense to configure them next to each other.

**Django**
   Django has to date unfortunately no concept of an application assembler or "app is done" hooks.
   Therefore the bottom of your ``settings.py`` will have to do.

**Flask**
   See `Logging Application Errors <http://flask.pocoo.org/docs/errorhandling/>`_.

**Pyramid**
   `Application constructor <http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/startup.html#the-startup-process>`_.

**Twisted**
   The `plugin definition <http://twistedmatrix.com/documents/current/core/howto/plugin.html>`_ is the best place.
   If your app is not a plugin, put it into your `tac file <http://twistedmatrix.com/documents/current/core/howto/application.html>`_ (and then `learn <https://bitbucket.org/jerub/twisted-plugin-example>`_ about plugins).

If you have no choice but *have* to configure on import time in module-global scope, or can't rule out for other reasons that that your :func:`structlog.configure` gets called more than once, structlog offers :func:`structlog.configure_once` that raises a warning if structlog has been configured before (no matter whether using :func:`structlog.configure` or :func:`~structlog.configure_once`) but doesn't change anything.


Immutability
------------

   You should call some functions with some arguments.

   ---David Reid

The behavior of copying itself, adding new values, and returning the result is useful for applications that keep somehow their own context using classes or closures.
Twisted is a :ref:`fine example <twisted-example>` for that.
Another possible approach is passing wrapped loggers around or log only within your view where you gather errors and events using return codes and exceptions.
If you are willing to do that, you should stick to it because `immutable state <http://en.wikipedia.org/wiki/Immutable_object>`_ is a very good thing\ [*]_.
Sooner or later, global state and mutable data lead to unpleasant surprises.

However, in the case of conventional web development, we realize that passing loggers around seems rather cumbersome, intrusive, and generally against the mainstream culture.
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

.. doctest::

   >>> from structlog.threadlocal import wrap_dict
   >>> WrappedDictClass = wrap_dict(dict)
   >>> d1 = WrappedDictClass({'a': 1})
   >>> d2 = WrappedDictClass({'b': 2})
   >>> d3 = WrappedDictClass()
   >>> d3['c'] = 3
   >>> d1 is d3
   False
   >>> d1 == d2 == d3 == WrappedDictClass()
   True
   >>> d3  # doctest: +ELLIPSIS
   <WrappedDict-...({'a': 1, 'c': 3, 'b': 2})>


Then use an instance of the generated class as the context class::

   configure(context_class=WrappedDictClass())

.. note::
   **Remember**: the instance of the class *doesn't* matter.
   Only the class *type* matters because *all* instances of one class *share* the *same* data.

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


In order to be able to bind values temporarily to a logger, :mod:`structlog.threadlocal` comes with a `context manager <http://docs.python.org/2/library/stdtypes.html#context-manager-types>`_: :func:`~structlog.threadlocal.tmp_bind`\ :

.. testsetup:: ctx

   from structlog import PrintLogger, wrap_logger
   from structlog.threadlocal import tmp_bind, wrap_dict
   WrappedDictClass = wrap_dict(dict)
   log = wrap_logger(PrintLogger(), context_class=WrappedDictClass)

.. doctest:: ctx

   >>> log.bind(x=42)  # doctest: +ELLIPSIS
   <BoundLogger(context=<WrappedDict-...({'x': 42})>, ...)>
   >>> log.msg('event!')
   x=42 event='event!'
   >>> with tmp_bind(log, x=23, y='foo') as tmp_log:
   ...     tmp_log.msg('another event!')
   y='foo' x=23 event='another event!'
   >>> log.msg('one last event!')
   x=42 event='one last event!'

The state before the ``with`` statement is saved and restored once it's left.

If you want to detach a logger from thread local data, there's :func:`structlog.threadlocal.as_immutable`.


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
     See :ref:`configuration` for more details.

The general sentiment against thread locals is that they're hard to test.
In this case we feel like this is an acceptable trade-off.
You can easily write deterministic tests using a call-capturing processor if you use the API properly (cf. warning above).

This big red box is also what separates immutable local from mutable global data.


.. [*] Special care has been taken to detect and support greenlets properly.

.. _OrderedDict: http://docs.python.org/2/library/collections.html#collections.OrderedDict
