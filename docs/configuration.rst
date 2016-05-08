.. _configuration:

Configuration
=============


Global Defaults
---------------

To make logging as unintrusive and straight-forward to use as possible, ``structlog`` comes with a plethora of configuration options and convenience functions.
Let me start at the end and introduce you to the ultimate convenience function that relies purely on configuration: :func:`structlog.get_logger` (and its Twisted-friendly alias :func:`structlog.getLogger`).

The goal is to reduce your per-file logging boilerplate to::

   from structlog import get_logger
   logger = get_logger()

while still giving you the full power via configuration.

To achieve that you'll have to call :func:`structlog.configure` on app initialization (of course, only if you're not content with the defaults).
The :ref:`example <proc>` from the previous chapter could thus have been written as following:

.. testcleanup:: *

   import structlog
   structlog.reset_defaults()

.. testsetup:: config_wrap_logger, config_get_logger

   from structlog import PrintLogger, configure, reset_defaults, wrap_logger, get_logger
   from structlog.threadlocal import wrap_dict
   def proc(logger, method_name, event_dict):
      print('I got called with', event_dict)
      return repr(event_dict)

.. doctest:: config_wrap_logger

   >>> configure(processors=[proc], context_class=dict)
   >>> log = wrap_logger(PrintLogger())
   >>> log.msg('hello world')
   I got called with {'event': 'hello world'}
   {'event': 'hello world'}

In fact, it could even be written like

.. doctest:: config_get_logger

   >>> configure(processors=[proc], context_class=dict)
   >>> log = get_logger()
   >>> log.msg('hello world')
   I got called with {'event': 'hello world'}
   {'event': 'hello world'}

because :class:`~structlog.processors.PrintLogger` is the default ``LoggerFactory`` used (see :ref:`logger-factories`).

``structlog`` tries to behave in the least surprising way when it comes to handling defaults and configuration:

#. Arguments passed to :func:`structlog.wrap_logger` *always* take the highest precedence over configuration.
   That means that you can overwrite whatever you've configured for each logger respectively.
#. If you leave them on `None`, ``structlog`` will check whether you've configured default values using :func:`structlog.configure` and uses them if so.
#. If you haven't configured or passed anything at all, the default fallback values are used which means :class:`collections.OrderedDict` for context and ``[``:class:`~structlog.processors.StackInfoRenderer`, :func:`~structlog.processors.format_exc_info`, :class:`~structlog.processors.KeyValueRenderer`\ ``]`` for the processor chain, and `False` for `cache_logger_on_first_use`.

If necessary, you can always reset your global configuration back to default values using :func:`structlog.reset_defaults`.
That can be handy in tests.

.. note::

   Since you will call :func:`structlog.wrap_logger` (or one of the ``get_logger()`` functions) most likely at import time and thus before you had a chance to configure ``structlog``, they return a **proxy** that returns a correct wrapped logger on first ``bind()``/``new()``.

   Therefore, you must not call ``new()`` or ``bind()`` in module scope!
   Use :func:`~structlog.get_logger`\ 's ``initial_values`` to achieve pre-populated contexts.

   To enable you to log with the module-global logger, it will create a temporary BoundLogger and relay the log calls to it on *each call*.
   Therefore if you have nothing to bind but intend to do lots of log calls in a function, it makes sense performance-wise to create a local logger by calling ``bind()`` or ``new()`` without any parameters.
   See also :doc:`performance`.


.. _logger-factories:

Logger Factories
----------------

To make :func:`structlog.get_logger` work, one needs one more option that hasn't been discussed yet: ``logger_factory``.

It is a callable that returns the logger that gets wrapped and returned.
In the simplest case, it's a function that returns a logger -- or just a class.
But you can also pass in an instance of a class with a ``__call__`` method for more complicated setups.

.. versionadded:: 0.4.0
   :func:`structlog.get_logger` can optionally take positional parameters.

These will be passed to the logger factories.
For example, if you use run ``structlog.get_logger('a name')`` and configure ``structlog`` to use the standard library :class:`~structlog.stdlib.LoggerFactory` which has support for positional parameters, the returned logger will have the name ``'a name'``.

When writing custom logger factories, they should always accept positional parameters even if they don't use them.
That makes sure that loggers are interchangeable.

For the common cases of standard library logging and Twisted logging, ``structlog`` comes with two factories built right in:

- :class:`structlog.stdlib.LoggerFactory`
- :class:`structlog.twisted.LoggerFactory`

So all it takes to use ``structlog`` with standard library logging is this::

   >>> from structlog import get_logger, configure
   >>> from structlog.stdlib import LoggerFactory
   >>> configure(logger_factory=LoggerFactory())
   >>> log = get_logger()
   >>> log.critical('this is too easy!')
   event='this is too easy!'

By using ``structlog``'s :class:`structlog.stdlib.LoggerFactory`, it is also ensured that variables like function names and line numbers are expanded correctly in your log format.

The :ref:`Twisted example <twisted-example>` shows how easy it is for Twisted.

.. note::

   `LoggerFactory()`-style factories always need to get passed as *instances* like in the examples above.
   While neither allows for customization using parameters yet, they may do so in the future.

Calling :func:`structlog.get_logger` without configuration gives you a perfectly useful :class:`structlog.PrintLogger` with the default values explained above.
I don't believe silent loggers are a sensible default.


Where to Configure
------------------

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
   The `plugin definition <https://twistedmatrix.com/documents/current/core/howto/plugin.html>`_ is the best place.
   If your app is not a plugin, put it into your `tac file <https://twistedmatrix.com/documents/current/core/howto/application.html>`_ (and then `learn <https://bitbucket.org/jerub/twisted-plugin-example>`_ about plugins).

If you have no choice but *have* to configure on import time in module-global scope, or can't rule out for other reasons that that your :func:`structlog.configure` gets called more than once, ``structlog`` offers :func:`structlog.configure_once` that raises a warning if ``structlog`` has been configured before (no matter whether using :func:`structlog.configure` or :func:`~structlog.configure_once`) but doesn't change anything.
