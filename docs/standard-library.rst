Python Standard Library
=======================


Concrete Bound Logger
---------------------

To make structlog's behavior less magicy, it ships with a standard library-specific wrapper class that has an explicit API instead of improvising: :class:`structlog.stdlib.BoundLogger`.
It behaves exactly like the generic :class:`structlog.BoundLogger` except:

- it's slightly faster due to less overhead,
- has an explicit API that mirrors the log methods of standard library's Logger_,
- hence causing less cryptic error messages if you get method names wrong.


Processors
----------

structlog comes with one standard library-specific processor:

:func:`~structlog.stdlib.filter_by_level`:
   Checks the log entries's log level against the configuration of standard library's logging.
   Log entries below the threshold get silently dropped.
   Put it at the beginning of your processing chain to avoid expensive operations happen in the first place.


Suggested Configuration
-----------------------

::

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

See also :doc:`logging-best-practices`.


.. _Logger: http://docs.python.org/2/library/logging.html#logger-objects
