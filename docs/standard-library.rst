Python Standard Library
=======================

Ideally, ``structlog`` should be able to be used as a drop-in replacement for standard library's :mod:`logging` by wrapping it.
In other words, you should be able to replace your call to :func:`logging.getLogger` by a call to :func:`structlog.get_logger` and things should keep working as before (if ``structlog`` is configured right, see :ref:`stdlib-config` below).

If you run into incompatibilities, it is a *bug* so please take the time to `report it <https://github.com/hynek/structlog/issues>`_!
If you're a heavy :mod:`logging` user, your `help <https://github.com/hynek/structlog/issues?q=is%3Aopen+is%3Aissue+label%3Astdlib>`_ to ensure a better compatibility would be highly appreciated!


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

:func:`~structlog.stdlib.filter_by_level`:
   Checks the log entry's log level against the configuration of standard library's logging.
   Log entries below the threshold get silently dropped.
   Put it at the beginning of your processing chain to avoid expensive operations happen in the first place.

:func:`~structlog.stdlib.add_logger_name`:
   Adds the name of the logger to the event dictionary under the key ``logger``.

:func:`~structlog.stdlib.add_log_level`:
   Adds the log level to the event dictionary under the key ``level``.

:class:`~structlog.stdlib.PositionalArgumentsFormatter`:
   This processes and formats positional arguments (if any) passed to log methods in the same way the ``logging`` module would do, e.g. ``logger.info("Hello, %s", name)``.


.. _stdlib-config:

Suggested Configuration
-----------------------

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
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


To make your program behave like a proper `12 factor app`_ that outputs only JSON to ``stdout``, configure the ``logging`` module like this::

    import logging
    import sys

    handler = logging.StreamHandler(sys.stdout)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

If you plan to hook up the logging output to `logstash`, as suggested in :doc:`logging-best-practices`, the simplest approach is to configure ``logstash-forwarder`` to pick up the output from your application.
To achieve this, configure your process supervisor (such as ``runit`` or ``supervisord``) to store the output in a file, and have ``logstash-forwarder`` monitor that file to ship it to the central log collection server.
This approach also applies to other centralized logging solutions.

.. _`12 factor app`: http://12factor.net/logs
