.. _api:

API Reference
=============

.. note::
   The examples here use a very simplified configuration using the minimalistic `structlog.processors.KeyValueRenderer` for brevity and to enable doctests.
   The output is going to be different (nicer!) with the default configuration.


.. testsetup:: *

   import structlog
   structlog.configure(
       processors=[structlog.processors.KeyValueRenderer()],
   )

.. testcleanup:: *

   import structlog
   structlog.reset_defaults()


.. module:: structlog

`structlog` Package
-------------------

.. autofunction:: get_logger

.. autofunction:: getLogger

.. autofunction:: wrap_logger

.. autofunction:: configure

.. autofunction:: configure_once

.. autofunction:: reset_defaults

.. autofunction:: is_configured

.. autofunction:: get_config

.. autoclass:: BoundLogger
   :members: new, bind, unbind

.. autofunction:: get_context

.. autoclass:: PrintLogger
   :members: msg, err, debug, info, warning, error, critical, log, failure, fatal

.. autoclass:: PrintLoggerFactory

.. autoclass:: BytesLogger
   :members: msg, err, debug, info, warning, error, critical, log, failure, fatal

.. autoclass:: BytesLoggerFactory

.. autoexception:: DropEvent

.. autoclass:: BoundLoggerBase
   :members: new, bind, unbind, _logger, _process_event, _proxy_to_logger


`structlog.dev` Module
----------------------

.. automodule:: structlog.dev

.. autoclass:: ConsoleRenderer
    :members: get_default_level_styles

.. autofunction:: set_exc_info


`structlog.testing` Module
--------------------------

.. automodule:: structlog.testing

.. autofunction:: capture_logs
.. autoclass:: LogCapture
.. autoclass:: ReturnLogger
   :members: msg, err, debug, info, warning, error, critical, log, failure, fatal

.. autoclass:: ReturnLoggerFactory


`structlog.threadlocal` Module
------------------------------

.. automodule:: structlog.threadlocal

.. autofunction:: merge_threadlocal

.. autofunction:: clear_threadlocal

.. autofunction:: bind_threadlocal

.. autofunction:: wrap_dict

.. autofunction:: tmp_bind(logger, **tmp_values)

   >>> from structlog import wrap_logger, PrintLogger
   >>> from structlog.threadlocal import tmp_bind, wrap_dict
   >>> logger = wrap_logger(PrintLogger(),  context_class=wrap_dict(dict))
   >>> with tmp_bind(logger, x=5) as tmp_logger:
   ...     logger = logger.bind(y=3)
   ...     tmp_logger.msg("event")
   x=5 y=3 event='event'
   >>> logger.msg("event")
   event='event'


.. autofunction:: as_immutable


`structlog.contextvars` Module
------------------------------

.. automodule:: structlog.contextvars

.. autofunction:: merge_contextvars
.. autofunction:: clear_contextvars
.. autofunction:: bind_contextvars
.. autofunction:: unbind_contextvars


.. _procs:

`structlog.processors` Module
-----------------------------

.. automodule:: structlog.processors

.. autoclass:: JSONRenderer

   .. doctest::

      >>> from structlog.processors import JSONRenderer
      >>> JSONRenderer(sort_keys=True)(None, None, {"a": 42, "b": [1, 2, 3]})
      '{"a": 42, "b": [1, 2, 3]}'

   Bound objects are attempted to be serialize using a ``__structlog__`` method.
   If none is defined, ``repr()`` is used:

   .. doctest::

      >>> class C1:
      ...     def __structlog__(self):
      ...         return ["C1!"]
      ...     def __repr__(self):
      ...         return "__structlog__ took precedence"
      >>> class C2:
      ...     def __repr__(self):
      ...         return "No __structlog__, so this is used."
      >>> from structlog.processors import JSONRenderer
      >>> JSONRenderer(sort_keys=True)(None, None, {"c1": C1(), "c2": C2()})
      '{"c1": ["C1!"], "c2": "No __structlog__, so this is used."}'

   Please note that additionally to strings, you can also return any type the standard library JSON module knows about -- like in this example a list.

   If you choose to pass a *default* parameter as part of *json_kw*, support for ``__structlog__`` is disabled.
   This can be useful when used together with more elegant serialization methods like :func:`functools.singledispatch`: `Better Python Object Serialization <https://hynek.me/articles/serialization/>`_.

.. autoclass:: KeyValueRenderer

   .. doctest::

      >>> from structlog.processors import KeyValueRenderer
      >>> KeyValueRenderer(sort_keys=True)(None, None, {"a": 42, "b": [1, 2, 3]})
      'a=42 b=[1, 2, 3]'
      >>> KeyValueRenderer(key_order=["b", "a"])(None, None,
      ...                                       {"a": 42, "b": [1, 2, 3]})
      'b=[1, 2, 3] a=42'


.. autoclass:: UnicodeDecoder

.. autoclass:: UnicodeEncoder

.. autofunction:: format_exc_info

   .. doctest::

      >>> from structlog.processors import format_exc_info
      >>> try:
      ...     raise ValueError
      ... except ValueError:
      ...     format_exc_info(None, None, {"exc_info": True})  # doctest: +ELLIPSIS
      {'exception': 'Traceback (most recent call last):...

.. autoclass:: StackInfoRenderer

.. autoclass:: ExceptionPrettyPrinter

.. autoclass:: TimeStamper

   .. doctest::

      >>> from structlog.processors import TimeStamper
      >>> TimeStamper()(None, None, {})  # doctest: +SKIP
      {'timestamp': 1378994017}
      >>> TimeStamper(fmt="iso")(None, None, {})  # doctest: +SKIP
      {'timestamp': '2013-09-12T13:54:26.996778Z'}
      >>> TimeStamper(fmt="%Y", key="year")(None, None, {})  # doctest: +SKIP
      {'year': '2013'}


`structlog.stdlib` Module
-------------------------

.. automodule:: structlog.stdlib

.. autofunction:: get_logger

.. autoclass:: BoundLogger
   :members: bind, unbind, new, debug, info, warning, warn, error, critical, exception, log

.. autoclass:: LoggerFactory
   :members: __call__

.. autofunction:: render_to_log_kwargs

.. autofunction:: filter_by_level

.. autofunction:: add_log_level

.. autofunction:: add_log_level_number

.. autofunction:: add_logger_name

.. autoclass:: PositionalArgumentsFormatter

.. autoclass:: ProcessorFormatter
   :members: wrap_for_formatter


`structlog.types` Module
------------------------

.. automodule:: structlog.types

.. autoprotocol:: BindableLogger

   Additionally to the methods listed below, bound loggers **must** have a ``__init__`` method with the following signature:

   .. method:: __init__(self, wrapped_logger: WrappedLogger, processors: Iterable[Processor], context: Context) -> None
      :noindex:

   Unfortunately it's impossible to define initializers using `PEP 544 <https://www.python.org/dev/peps/pep-0544/>`_ Protocols.

   They currently also have to carry a `Context` as a ``_context`` attribute.

.. autodata:: EventDict
.. autodata:: WrappedLogger
.. autodata:: Processor
.. autodata:: Context
.. autodata:: ExcInfo


`structlog.twisted` Module
--------------------------

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
