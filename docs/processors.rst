Processors
==========

The true power of ``structlog`` lies in its *combinable log processors*.
A log processor is a regular callable, i.e. a function or an instance of a class with a ``__call__()`` method.

.. _chains:

Chains
------

The *processor chain* is a list of processors.
Each processors receives three positional arguments:

**logger**
   Your wrapped logger object.
   For example `logging.Logger`.

**method_name**
   The name of the wrapped method.
   If you called ``log.warning("foo")``, it will be ``"warning"``.

**event_dict**
   Current context together with the current event.
   If the context was ``{"a": 42}`` and the event is ``"foo"``, the initial ``event_dict`` will be ``{"a":42, "event": "foo"}``.

The return value of each processor is passed on to the next one as ``event_dict`` until finally the return value of the last processor gets passed into the wrapped logging method.


Examples
^^^^^^^^

If you set up your logger like:

.. code:: python

   from structlog import PrintLogger, wrap_logger
   wrapped_logger = PrintLogger()
   logger = wrap_logger(wrapped_logger, processors=[f1, f2, f3, f4])
   log = logger.new(x=42)

and call ``log.msg("some_event", y=23)``, it results in the following call chain:

.. code:: python

   wrapped_logger.msg(
      f4(wrapped_logger, "msg",
         f3(wrapped_logger, "msg",
            f2(wrapped_logger, "msg",
               f1(wrapped_logger, "msg", {"event": "some_event", "x": 42, "y": 23})
            )
         )
      )
   )

In this case, ``f4`` has to make sure it returns something ``wrapped_logger.msg`` can handle (see :ref:`adapting`).
For the example with ``PrintLogger`` above, this means ``f4`` must return a string.

The simplest modification a processor can make is adding new values to the ``event_dict``.
Parsing human-readable timestamps is tedious, not so `UNIX timestamps <https://en.wikipedia.org/wiki/UNIX_time>`_ -- let's add one to each log entry!

.. literalinclude:: code_examples/processors/timestamper.py
   :language: python

Please note, that ``structlog`` comes with such a processor built in: `TimeStamper`.


Filtering
---------

If a processor raises `structlog.DropEvent`, the event is silently dropped.

Therefore, the following processor drops every entry:

.. literalinclude:: code_examples/processors/dropper.py
   :language: python

But we can do better than that!

.. _cond_drop:

How about dropping only log entries that are marked as coming from a certain peer (e.g. monitoring)?

.. literalinclude:: code_examples/processors/conditional_dropper.py
   :language: python


Since it's so common to filter by the log level, ``structlog`` comes with `structlog.make_filtering_bound_logger` that filters log entries before they even enter the processor chain..
It does **not** use the standard library, but it does use its names and order of log levels.
In practice, it only looks up the numeric value of the method name and compares it to the configured minimal level.
That's fast and usually good enough for applications.


.. _adapting:

Adapting and Rendering
----------------------

An important role is played by the *last* processor because its duty is to adapt the ``event_dict`` into something the underlying logging method understands.
With that, it's also the *only* processor that needs to know anything about the underlying system.

It can return one of three types:

- An Unicode string or a bytes string (i.e. `str` or `bytes`) that is passed as the first (and only) positional argument to the underlying logger.
- A tuple of ``(args, kwargs)`` that are passed as ``log_method(*args, **kwargs)``.
- A dictionary which is passed as ``log_method(**kwargs)``.

Therefore ``return "hello world"`` is a shortcut for ``return (("hello world",), {})`` (the example in `chains` assumes this shortcut has been taken).

This should give you enough power to use ``structlog`` with any logging system while writing agnostic processors that operate on dictionaries.

.. versionchanged:: 14.0.0
   Allow final processor to return a `dict`.


Examples
^^^^^^^^

The probably most useful formatter for string based loggers is `structlog.processors.JSONRenderer`.
Advanced log aggregation and analysis tools like `logstash <https://www.elastic.co/products/logstash>`_ offer features like telling them "this is JSON, deal with it" instead of fiddling with regular expressions.

More examples can be found in the :ref:`examples <processors-examples>` chapter.
For a list of shipped processors, check out the :ref:`API documentation <procs>`.


Third Party Packages
--------------------

Since processors are self-contained callables, it's easy to write your own and to share them in separate packages.

We collect those packages in our `GitHub Wiki <https://github.com/hynek/structlog/wiki/Third-Party-Extensions>`_ and encourage you to add your package too!
