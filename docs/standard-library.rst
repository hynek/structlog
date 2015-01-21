Python Standard Library
=======================

Ideally, structlog should be able to be used as a drop-in replacement for standard library's :mod:`logging` by wrapping it.
In other words, you should be able to replace your call to :func:`logging.getLogger` by a call to :func:`structlog.get_logger` and things should keep working as before (if structlog is configured right, see :ref:`stdlib-config` below).

If you run into incompatibilities, it is a *bug* so please take the time to `report it <https://github.com/hynek/structlog/issues>`_!
If you're a heavy :mod:`logging` user, your `help <https://github.com/hynek/structlog/issues?q=is%3Aopen+is%3Aissue+label%3Astdlib>`_ to ensure a better compatibility would be highly appreciated!


Concrete Bound Logger
---------------------

To make structlog's behavior less magicy, it ships with a standard library-specific wrapper class that has an explicit API instead of improvising: :class:`structlog.stdlib.BoundLogger`.
It behaves exactly like the generic :class:`structlog.BoundLogger` except:

- it's slightly faster due to less overhead,
- has an explicit API that mirrors the log methods of standard library's :class:`logging.Logger`,
- hence causing less cryptic error messages if you get method names wrong.


Processors
----------

structlog comes with one standard library-specific processor:

:func:`~structlog.stdlib.filter_by_level`:
   Checks the log entries's log level against the configuration of standard library's logging.
   Log entries below the threshold get silently dropped.
   Put it at the beginning of your processing chain to avoid expensive operations happen in the first place.


.. _stdlib-config:

Suggested Configuration
-----------------------

A basic configuration to output structured logs in JSON format looks like this::

   import structlog

   structlog.configure(
      processors=[
          structlog.stdlib.filter_by_level,
          structlog.processors.StackInfoRenderer(),
          structlog.processors.format_exc_info,
          structlog.processors.JSONRenderer()
      ],
      context_class=dict,
      logger_factory=structlog.stdlib.LoggerFactory(),
      wrapper_class=structlog.stdlib.BoundLogger,
      cache_logger_on_first_use=True,
   )

If you plan to hook up the logging output to `logstash`, as suggested in :doc:`logging-best-practices`, you can simply output JSON, and have ``logstash-forwarder`` pick that up.
To do so, you need to configure your process supervisor (such ``runit`` or ``supervisord``) to store the output in a file that is subsequently monitored by ``logstash-forwarder``, or alternatively you could pipe the output directly into ``logstash-forwarder``.
To make your program behave like a proper `12 factor app`_ that outputs JSON to ``stdout``, configure the ``logging`` module like this::

    import logging
    import sys

    handler = logging.StreamHandler(sys.stdout)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

Note that the above ``structlog`` configuration does not include the log level, logger name, or time stamp in the JSON output.
If you want to include those, just add processors to take care of this, e.g.::

    def add_log_level(logger, method_name, event_dict):
        if method_name == 'warn':  # stdlib alias
            method_name == 'warning'
        event_dict['level'] = method_name
        return event_dict

    def add_logger_name(logger, method_name, event_dict):
        event_dict['logger'] = logger.name
        return event_dict

Then extend the ``processors=...`` argument to ``structlog.configure()``, e.g.::

    [
        add_log_level,
        add_logger_name,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.stdlib.filter_by_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ]

.. _`12 factor app`: http://12factor.net/logs
