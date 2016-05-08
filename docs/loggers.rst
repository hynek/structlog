Loggers
=======


Bound Loggers
-------------

The center of ``structlog`` is the immutable log wrapper :class:`~structlog.BoundLogger`.

All it does is:

- Keep a *context dictionary* and a *logger* that it's wrapping,
- recreate itself with (optional) *additional* context data (the :func:`~structlog.BoundLogger.bind` and :func:`~structlog.BoundLogger.new` methods),
- recreate itself with *less* data (:func:`~structlog.BoundLogger.unbind`),
- and finally relay *all* other method calls to the wrapped logger\ [*]_ after processing the log entry with the configured chain of :ref:`processors <processors>`.

You won't be instantiating it yourself though.
For that there is the :func:`structlog.wrap_logger` function (or the convenience function :func:`structlog.get_logger` we'll discuss in a minute):

.. _proc:

.. doctest::

   >>> from structlog import wrap_logger
   >>> class PrintLogger(object):
   ...     def msg(self, message):
   ...         print(message)
   >>> def proc(logger, method_name, event_dict):
   ...     print('I got called with', event_dict)
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
   The one and only positional argument is the logger that you want to wrap and to which the log entries will be proxied.
   If you wish to use a :ref:`configured logger factory <logger-factories>`, set it to `None`.

**processors**
   A list of callables that can :ref:`filter, mutate, and format <processors>` the log entry before it gets passed to the wrapped logger.

   Default is ``[``:func:`~structlog.processors.format_exc_info`, :class:`~structlog.processors.KeyValueRenderer`\ ``]``.

**context_class**
   The class to save your context in.
   Particularly useful for :ref:`thread local context storage <threadlocal>`.

   Default is :class:`collections.OrderedDict`.

Additionally, the following arguments are allowed too:

**wrapper_class**
   A class to use instead of :class:`~structlog.BoundLogger` for wrapping.
   This is useful if you want to sub-class BoundLogger and add custom logging methods.
   BoundLogger's bind/new methods are sub-classing friendly so you won't have to re-implement them.
   Please refer to the :ref:`related example <wrapper_class-example>` for how this may look.

**initial_values**
   The values that new wrapped loggers are automatically constructed with.
   Useful for example if you want to have the module name as part of the context.

.. note::

   Free your mind from the preconception that log entries have to be serialized to strings eventually.
   All ``structlog`` cares about is a *dictionary* of *keys* and *values*.
   What happens to it depends on the logger you wrap and your processors alone.

   This gives you the power to log directly to databases, log aggregation servers, web services, and whatnot.


Printing and Testing
--------------------

To save you the hassle of using standard library logging for simple standard out logging, ``structlog`` ships a :class:`~structlog.PrintLogger` that can log into arbitrary files -- including standard out (which is the default if no file is passed into the constructor):

.. doctest::

   >>> from structlog import PrintLogger
   >>> PrintLogger().info('hello world!')
   hello world!

It's handy for both examples and in combination with tools like `runit <http://smarden.org/runit/>`_ or `stdout/stderr-forwarding <https://hynek.me/articles/taking-some-pain-out-of-python-logging/>`_.

Additionally -- mostly for unit testing -- ``structlog`` also ships with a logger that just returns whatever it gets passed into it: :class:`~structlog.ReturnLogger`.

.. doctest::

   >>> from structlog import ReturnLogger
   >>> ReturnLogger().msg(42) == 42
   True
   >>> obj = ['hi']
   >>> ReturnLogger().msg(obj) is obj
   True
   >>> ReturnLogger().msg('hello', when='again')
   (('hello',), {'when': 'again'})


.. [*] Since this is slightly magicy, ``structlog`` comes with concrete loggers for the :doc:`standard-library` and :doc:`twisted` that offer you explicit APIs for the supported logging methods but behave identically like the generic BoundLogger otherwise.
