.. _api:

API Reference
=============

.. module:: structlog

:mod:`structlog` Package
------------------------

.. autofunction:: get_logger

.. autofunction:: getLogger

.. autofunction:: wrap_logger

.. autofunction:: configure

.. autofunction:: configure_once

.. autofunction:: reset_defaults

.. autoclass:: BoundLogger
   :members: new, bind, unbind

.. autoclass:: PrintLogger
   :members: msg, err, debug, info, warning, error, critical, log, failure

.. autoclass:: PrintLoggerFactory

.. autoclass:: ReturnLogger
   :members: msg, err, debug, info, warning, error, critical, log, failure

.. autoclass:: ReturnLoggerFactory

.. autoexception:: DropEvent

.. autoclass:: BoundLoggerBase
   :members: new, bind, unbind, _logger, _process_event, _proxy_to_logger


:mod:`dev` Module
-----------------

.. automodule:: structlog.dev

.. autoclass:: ConsoleRenderer


:mod:`threadlocal` Module
-------------------------

.. automodule:: structlog.threadlocal

.. autofunction:: wrap_dict

.. autofunction:: tmp_bind(logger, **tmp_values)

.. autofunction:: as_immutable


.. _procs:

:mod:`processors` Module
------------------------

.. automodule:: structlog.processors

.. autoclass:: JSONRenderer

.. autoclass:: KeyValueRenderer

.. autoclass:: UnicodeDecoder

.. autoclass:: UnicodeEncoder

.. autofunction:: format_exc_info

.. autoclass:: StackInfoRenderer

.. autoclass:: ExceptionPrettyPrinter

.. autoclass:: TimeStamper(fmt=None, utc=True)


:mod:`stdlib` Module
--------------------

.. automodule:: structlog.stdlib

.. autoclass:: BoundLogger
   :members: bind, unbind, new, debug, info, warning, warn, error, critical, exception, log

.. autoclass:: LoggerFactory
   :members: __call__

.. autofunction:: filter_by_level

.. autofunction:: add_log_level

.. autofunction:: add_logger_name

.. autoclass:: PositionalArgumentsFormatter


:mod:`twisted` Module
---------------------

.. automodule:: structlog.twisted

.. autoclass:: BoundLogger
   :members: bind, unbind, new, msg, err

.. autoclass:: LoggerFactory
   :members: __call__

.. autoclass:: EventAdapter

.. autoclass:: JSONRenderer

.. autofunction:: plainJSONStdOutLogger

.. autofunction:: JSONLogObserverWrapper

.. autoclass:: PlainFileLogObserver
