Standard Library Logging
========================

Ideally, ``structlog`` should be able to be used as a drop-in replacement for standard library's :mod:`logging` by wrapping it.
In other words, you should be able to replace your call to :func:`logging.getLogger` by a call to :func:`structlog.get_logger` and things should keep working as before (if ``structlog`` is configured right, see :ref:`stdlib-config` below).

If you run into incompatibilities, it is a *bug* so please take the time to `report it <https://github.com/hynek/structlog/issues>`_!
If you're a heavy :mod:`logging` user, your `help <https://github.com/hynek/structlog/issues?q=is%3Aopen+is%3Aissue+label%3Astdlib>`_ to ensure a better compatibility would be highly appreciated!


Just Enough ``logging``
-----------------------

If you want to use ``structlog`` with :mod:`logging`, you still have to have at least fleeting understanding on how the standard library operates because ``structlog`` will *not* do any magic things in the background for you.
Most importantly you have to *configure* the :mod:`logging` system *additionally* to configuring ``structlog``.

Usually it is enough to use::

  import logging
  import sys

  logging.basicConfig(
      format="%(message)s",
      stream=sys.stdout,
      level=logging.INFO,
  )

This will send all log messages with the `log level <https://docs.python.org/3/library/logging.html#logging-levels>`_ ``logging.INFO`` and above (that means that e.g. :func:`logging.debug` calls are ignored) to standard out without any special formatting by the standard library.

If you require more complex behavior, please refer to the standard library's :mod:`logging` documentation.


Concrete Bound Logger
---------------------

To make ``structlog``'s behavior less magicy, it ships with a standard library-specific wrapper class that has an explicit API instead of improvising: :class:`structlog.stdlib.BoundLogger`.
It behaves exactly like the generic :class:`structlog.BoundLogger` except:

- it's slightly faster due to less overhead,
- has an explicit API that mirrors the log methods of standard library's :class:`logging.Logger`,
- hence causing less cryptic error messages if you get method names wrong.


Processors
----------

``structlog`` comes with a few standard library-specific processors:

:func:`~structlog.stdlib.render_to_log_kwargs`:
   Renders the event dictionary into keyword arguments for :func:`logging.log` that attaches everything except the `event` field to the *extra* argument.
   This is useful if you want to render your log entries entirely within :mod:`logging`.

:func:`~structlog.stdlib.filter_by_level`:
   Checks the log entry's log level against the configuration of standard library's logging.
   Log entries below the threshold get silently dropped.
   Put it at the beginning of your processing chain to avoid expensive operations from happening in the first place.

:func:`~structlog.stdlib.add_logger_name`:
   Adds the name of the logger to the event dictionary under the key ``logger``.

:func:`~structlog.stdlib.add_log_level`:
   Adds the log level to the event dictionary under the key ``level``.

:func:`~structlog.stdlib.add_log_level_number`:
   Adds the log level number to the event dictionary under the key ``level_number``.
   Log level numbers map to the log level names.
   The Python stdlib uses them for filtering logic.
   This adds the same numbers so users can leverage similar filtering.
   Compare::
   
      level in ("warning", "error", "critical")
      level_number >= 30

   The mapping of names to numbers is in :data:`~structlog.stdlib._NAME_TO_LEVEL`

:class:`~structlog.stdlib.PositionalArgumentsFormatter`:
   This processes and formats positional arguments (if any) passed to log methods in the same way the ``logging`` module would do, e.g. ``logger.info("Hello, %s", name)``.


``structlog`` also comes with :class:`~structlog.stdlib.ProcessorFormatter` which is a :class:`logging.Formatter` that enables you to format non-``structlog`` log entries using ``structlog`` renderers *and* multiplex ``structlog``’s output with different renderers (see below for an example).


.. _stdlib-config:

Suggested Configurations
------------------------

Depending *where* you'd like to do your formatting, you can take one of three approaches:


Rendering Using :mod:`logging`-based Formatters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import structlog

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

Now you have the event dict available within each log record.
If you want all your log entries (i.e. also those not from your app/``structlog``) to be formatted as JSON, you can use the `python-json-logger library <https://github.com/madzak/python-json-logger>`_:

.. code-block:: python

    import logging
    import sys

    from pythonjsonlogger import jsonlogger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(jsonlogger.JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

Now both ``structlog`` and ``logging`` will emit JSON logs:

.. code-block:: pycon

    >>> structlog.get_logger("test").warning("hello")
    {"message": "hello", "logger": "test", "level": "warning"}

    >>> logging.getLogger("test").warning("hello")
    {"message": "hello"}


Rendering Using ``structlog``-based Formatters Within :mod:`logging`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``structlog`` comes with a :class:`~structlog.stdlib.ProcessorFormatter` that can be used as a :class:`~logging.Formatter` in any stdlib :mod:`Handler <logging.handlers>` object.

The :class:`~structlog.stdlib.ProcessorFormatter` has two parts to its API:

#. The :meth:`~structlog.stdlib.ProcessorFormatter.wrap_for_formatter` method must be used as the last processor in :func:`structlog.configure`,
   it converts the the processed event dict to something that the ``ProcessorFormatter`` understands.
#. The :class:`~structlog.stdlib.ProcessorFormatter` itself,
   which can wrap any ``structlog`` renderer to handle the output of both ``structlog`` and standard library events.

Thus, the simplest possible configuration looks like the following:

.. code-block:: python

    import logging
    import structlog

    structlog.configure(
        processors=[
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(),
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

which will allow both of these to work in other modules:

.. code-block:: pycon

    >>> import logging
    >>> import structlog

    >>> logging.getLogger("stdlog").info("woo")
    woo
    >>> structlog.get_logger("structlog").info("amazing", events="oh yes")
    amazing                        events=oh yes

Of course, you probably want timestamps and log levels in your output.
The :class:`~structlog.stdlib.ProcessorFormatter` has a ``foreign_pre_chain`` argument which is responsible for adding properties to events from the standard library -- i.e. that do not originate from a ``structlog`` logger -- and which should in general match the ``processors`` argument to :func:`structlog.configure` so you get a consistent output.

For example, to add timestamps, log levels, and traceback handling to your logs you should do:

.. code-block:: python

    timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
    shared_processors = [
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(),
        foreign_pre_chain=shared_processors,
    )

which (given the same ``logging.*`` calls as in the previous example) will result in:

.. code-block:: pycon

    >>> logging.getLogger("stdlog").info("woo")
    2017-03-06 14:59:20 [info     ] woo
    >>> structlog.get_logger("structlog").info("amazing", events="oh yes")
    2017-03-06 14:59:20 [info     ] amazing                        events=oh yes

This allows you to set up some sophisticated logging configurations.
For example, to use the standard library's :func:`~logging.config.dictConfig` to log colored logs to the console and plain logs to a file you could do:

.. code-block:: python

    import logging.config
    import structlog

    timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
    pre_chain = [
        # Add the log level and a timestamp to the event_dict if the log entry
        # is not from structlog.
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "plain": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(colors=False),
                    "foreign_pre_chain": pre_chain,
                },
                "colored": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(colors=True),
                    "foreign_pre_chain": pre_chain,
                },
            },
            "handlers": {
                "default": {
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                    "formatter": "colored",
                },
                "file": {
                    "level": "DEBUG",
                    "class": "logging.handlers.WatchedFileHandler",
                    "filename": "test.log",
                    "formatter": "plain",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default", "file"],
                    "level": "DEBUG",
                    "propagate": True,
                },
            }
    })
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

This defines two formatters: one plain and one colored.
Both are run for each log entry.
Log entries that do not originate from ``structlog``, are additionally pre-processed using a cached ``timestamper`` and :func:`~structlog.stdlib.add_log_level`.

.. code-block:: pycon

    >>> logging.getLogger().warning("bar")
    2017-03-06 11:49:27 [warning  ] bar

    >>> structlog.get_logger("structlog").warning("foo", x=42)
    2017-03-06 11:49:32 [warning  ] foo                            x=42

    >>> print(open("test.log").read())
    2017-03-06 11:49:27 [warning  ] bar
    2017-03-06 11:49:32 [warning  ] foo                            x=42

(Sadly, you have to imagine the colors in the first two outputs.)

If you leave ``foreign_pre_chain`` as `None`, formatting will be left to :mod:`logging`.
Meaning: you can define a ``format`` for :class:`~structlog.stdlib.ProcessorFormatter` too!


Rendering Within ``structlog``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A basic configuration to output structured logs in JSON format looks like this:

.. code-block:: python

    import structlog

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

(If you're still runnning Python 2, replace :class:`~structlog.processors.UnicodeDecoder` through :class:`~structlog.processors.UnicodeEncoder`.)

To make your program behave like a proper `12 factor app`_ that outputs only JSON to ``stdout``, configure the ``logging`` module like this::

  import logging
  import sys

  logging.basicConfig(
      format="%(message)s",
      stream=sys.stdout,
      level=logging.INFO,
  )

In this case *only* your own logs are formatted as JSON:

.. code-block:: pycon

    >>> structlog.get_logger("test").warning("hello")
    {"event": "hello", "logger": "test", "level": "warning", "timestamp": "2017-03-06T07:39:09.518720Z"}

    >>> logging.getLogger("test").warning("hello")
    hello

.. _`12 factor app`: https://12factor.net/logs
