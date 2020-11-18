Loggers
=======


Bound Loggers
-------------

The center of ``structlog`` is the immutable log wrapper :class:`~structlog.BoundLogger`.

.. image:: _static/BoundLogger.svg

What it does is:

- Store a *context dictionary* with key-value pairs that should be part of every log entry,
- store a list of :doc:`processors <processors>` that are called on every log entry,
- and store a *logger* that it's wrapping.
  This *can* be standard library's `logging.Logger` but absolutely doesn't have to.

To manipulate the context dictionary, it offers to:

- Recreate itself with (optional) *additional* context data: :func:`~structlog.BoundLogger.bind` and :func:`~structlog.BoundLogger.new`.
- Recreate itself with *less* context data: :func:`~structlog.BoundLogger.unbind`.

In any case, the original bound logger or its context are never mutated.

Finally, if you call *any other* method on :class:`~structlog.BoundLogger`, it will:

#. Make a copy of the context -- now it becomes the *event dictionary*,
#. Add the keyword arguments of the method call to the event dict.
#. Add a new key ``event`` with the value of the first positional argument of the method call to the event dict.
#. Run the processors on the event dict.
   Each processor receives the result of its predecessor.
#. Finally it takes the result of the final processor and calls the method with the same name that got called on the bound logger on ther wrapped logger\ [1]_.
   For flexibility, the final processor can return either a string that is passed directly as a positional parameter, or a tuple ``(args, kwargs)`` that are passed as ``wrapped_logger.log_method(*args, **kwargs)``.


.. [1] Since this is slightly magicy, ``structlog`` comes with concrete loggers for the `standard-library` and :doc:`twisted` that offer you explicit APIs for the supported logging methods but behave identically like the generic BoundLogger otherwise.
       Of course, you are free to implement your own bound loggers too.


Creation
--------

You won't be instantiating it yourself though.
In practice you will configure ``structlog`` as explained in the `next chapter <configuration>`  and then just call `structlog.get_logger`.


In some rare cases you may not want to do that.
For that times there is the `structlog.wrap_logger` function that can be used to wrap a logger without any global state (i.e. configuration):

.. _proc:

.. doctest::

   >>> import structlog
   >>> class CustomPrintLogger:
   ...     def msg(self, message):
   ...         print(message)
   >>> def proc(logger, method_name, event_dict):
   ...     print("I got called with", event_dict)
   ...     return repr(event_dict)
   >>> log = structlog.wrap_logger(
   ...     CustomPrintLogger(),
   ...     wrapper_class=structlog.BoundLogger,
   ...     processors=[proc],
   ... )
   >>> log2 = log.bind(x=42)
   >>> log == log2
   False
   >>> log.msg("hello world")
   I got called with {'event': 'hello world'}
   {'event': 'hello world'}
   >>> log2.msg("hello world")
   I got called with {'x': 42, 'event': 'hello world'}
   {'x': 42, 'event': 'hello world'}
   >>> log3 = log2.unbind("x")
   >>> log == log3
   True
   >>> log3.msg("nothing bound anymore", foo="but you can structure the event too")
   I got called with {'foo': 'but you can structure the event too', 'event': 'nothing bound anymore'}
   {'foo': 'but you can structure the event too', 'event': 'nothing bound anymore'}

As you can see, it accepts one mandatory and a few optional arguments:

**logger**
   The one and only positional argument is the logger that you want to wrap and to which the log entries will be proxied.
   If you wish to use a :ref:`configured logger factory <logger-factories>`, set it to `None`.

**processors**
   A list of callables that can :doc:`filter, mutate, and format <processors>` the log entry before it gets passed to the wrapped logger.

   Default is ``[``:class:`~structlog.processors.StackInfoRenderer`, :func:`~structlog.processors.format_exc_info`, :class:`~structlog.processors.TimeStamper`, :class:`~structlog.dev.ConsoleRenderer`\ ``]``.

**context_class**
   The class to save your context in.
   Particularly useful for `thread local context storage <thread-local>`.

   Since Python 3.6+ and PyPy have ordered dictionaries, the default is a plain `dict`.

Additionally, the following arguments are allowed too:

**wrapper_class**
   A class to use instead of :class:`~structlog.BoundLogger` for wrapping.
   This is useful if you want to sub-class BoundLogger and add custom logging methods.
   BoundLogger's bind/new methods are sub-classing friendly so you won't have to re-implement them.
   Please refer to the :ref:`related example <wrapper_class-example>` for how this may look.

**initial_values**
   The values that new wrapped loggers are automatically constructed with.
   Useful, for example, if you want to have the module name as part of the context.

.. note::

   Free your mind from the preconception that log entries have to be serialized to strings eventually.
   All ``structlog`` cares about is a *dictionary* of *keys* and *values*.
   What happens to it depends on the logger you wrap and your processors alone.

   This gives you the power to log directly to databases, log aggregation servers, web services, and whatnot.
