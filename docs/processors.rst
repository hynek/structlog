.. _processors:

Processors
==========

The true power of ``structlog`` lies in its *combinable log processors*.
A log processor is a regular callable, i.e. a function or an instance of a class with a ``__call__()`` method.

.. _chains:

Chains
------

The *processor chain* is a plain Python list of processors.
Each processors receives three positional arguments:

#. the wrapped logger,
#. the name of the wrapped method,
#. and the current context together with the current event (called ``event_dict``).

The return value of each processor is passed on to the next one as ``event_dict`` until finally the return value of the last processor gets passed into the wrapped logging method.


Examples
++++++++

If you set up your logger like:

.. code:: python

   from structlog import BoundLogger, PrintLogger
   wrapped_logger = PrintLogger()
   logger = BoundLogger.wrap(wrapped_logger, processors=[f1, f2, f3, f4])
   log = logger.new(x=42)

and call ``log.msg('some_event', y=23)``, it results in the following call chain:

.. code:: python

   wrapped_logger.msg(
      f4(wrapped_logger, 'msg',
         f3(wrapped_logger, 'msg',
            f2(wrapped_logger, 'msg',
               f1(wrapped_logger, 'msg', {'event': 'some_event', 'x': 42, 'y': 23})
            )
         )
      )
   )

In this case, ``f4`` has to make sure it returns something ``wrapped_logger.msg`` can handle (see :ref:`adapting`).

The simplest modification a processor can make is adding new values to the ``event_dict``.
Parsing human-readable timestamps is tedious, not so `UNIX timestamps <http://en.wikipedia.org/wiki/UNIX_time>`_ -- let's add one to each log entry!

.. literalinclude:: code_examples/processors/timestamper.py
   :language: python

Easy, isn't it?
Please note, that structlog comes with such an processor built in: :class:`~structlog.processors.TimeStamper`.


Special Return Values
---------------------

There are two special return values that make the processor chain abort:

- ``False`` aborts the processor chain and the log entry is silently dropped.
- ``None`` raises an ``ValueError`` because you probably forgot to return a new value.


Examples
++++++++

The following processor simply drops every entry.

.. literalinclude:: code_examples/processors/dropper.py
   :language: python

But we can do better than that!

.. _cond_drop:

How about dropping only log entries that are marked as coming from a certain peer (e.g. monitoring)?

.. literalinclude:: code_examples/processors/conditional_dropper.py
   :language: python


.. _adapting:

Adapting and Rendering
----------------------

An important role is played by the *last* processor because its duty is to adapt the ``event_dict`` into something the underlying logging method understands.

For that, it can either return a string that is passed as the first (and only) positional argument to the underlying logger or a tuple of ``(args, kwargs)`` that are passed as ``log_method(*args, **kwargs)``.
Therefore ``return 'hello world'`` is a shortcut for ``return (('hello world',), {})`` (the example in :ref:`chains` assumes this shortcut has been taken).

This should give you enough power to use structlog with any logging system.

Examples
++++++++

The probably most useful formatter for string based loggers is :class:`~structlog.processors.JSONRenderer`.
Advanced log aggregation and analysis tools like `logstash <http://logstash.net>`_ offer features like telling them “this is JSON, deal with it” instead of fiddling with regular expressions.

More examples can be found in the :ref:`examples <processors-examples>` chapter.
