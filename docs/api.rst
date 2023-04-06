.. _api:

API Reference
=============

.. note::
   The examples here use a very simplified configuration using the minimalist `structlog.processors.KeyValueRenderer` for brevity and to enable doctests.
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

.. autofunction:: make_filtering_bound_logger

.. autofunction:: get_context

.. autoclass:: PrintLogger
   :members: msg, err, debug, info, warning, error, critical, log, failure, fatal

.. autoclass:: PrintLoggerFactory

.. autoclass:: WriteLogger
   :members: msg, err, debug, info, warning, error, critical, log, failure, fatal

.. autoclass:: WriteLoggerFactory

.. autoclass:: BytesLogger
   :members: msg, err, debug, info, warning, error, critical, log, failure, fatal

.. autoclass:: BytesLoggerFactory

.. autoexception:: DropEvent

.. autoclass:: BoundLoggerBase
   :members: new, bind, unbind, try_unbind, _logger, _process_event, _proxy_to_logger


`structlog.dev` Module
----------------------

.. automodule:: structlog.dev

.. autoclass:: ConsoleRenderer
   :members: get_default_level_styles

.. autofunction:: plain_traceback
.. autofunction:: rich_traceback
.. autofunction:: better_traceback

.. autofunction:: set_exc_info


`structlog.testing` Module
--------------------------

.. automodule:: structlog.testing

.. autofunction:: capture_logs
.. autoclass:: LogCapture

.. autoclass:: CapturingLogger

   >>> from pprint import pprint
   >>> cl = structlog.testing.CapturingLogger()
   >>> cl.info("hello")
   >>> cl.info("hello", when="again")
   >>> pprint(cl.calls)
   [CapturedCall(method_name='info', args=('hello',), kwargs={}),
    CapturedCall(method_name='info', args=('hello',), kwargs={'when': 'again'})]

.. autoclass:: CapturingLoggerFactory
.. autoclass:: CapturedCall

.. autoclass:: ReturnLogger
   :members: msg, err, debug, info, warning, error, critical, log, failure, fatal

.. autoclass:: ReturnLoggerFactory


`structlog.contextvars` Module
------------------------------

.. automodule:: structlog.contextvars

.. autofunction:: bind_contextvars
.. autofunction:: bound_contextvars
.. autofunction:: get_contextvars
.. autofunction:: get_merged_contextvars
.. autofunction:: merge_contextvars
.. autofunction:: clear_contextvars
.. autofunction:: unbind_contextvars
.. autofunction:: reset_contextvars

`structlog.threadlocal` Module
------------------------------

.. automodule:: structlog.threadlocal
   :noindex:


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

   .. tip::

      If you use this processor, you may also wish to add structured tracebacks for exceptions.
      You can do this by adding the :class:`~structlog.processors.dict_tracebacks` to your list of processors:

      .. doctest::

         >>> structlog.configure(
         ...     processors=[
         ...         structlog.processors.dict_tracebacks,
         ...         structlog.processors.JSONRenderer(),
         ...     ],
         ... )
         >>> log = structlog.get_logger()
         >>> var = "spam"
         >>> try:
         ...     1 / 0
         ... except ZeroDivisionError:
         ...     log.exception("Cannot compute!")
         {"event": "Cannot compute!", "exception": [{"exc_type": "ZeroDivisionError", "exc_value": "division by zero", "syntax_error": null, "is_cause": false, "frames": [{"filename": "<doctest default[3]>", "lineno": 2, "name": "<module>", "line": "", "locals": {..., "var": "spam"}}]}]}

.. autoclass:: KeyValueRenderer

   .. doctest::

      >>> from structlog.processors import KeyValueRenderer
      >>> KeyValueRenderer(sort_keys=True)(None, None, {"a": 42, "b": [1, 2, 3]})
      'a=42 b=[1, 2, 3]'
      >>> KeyValueRenderer(key_order=["b", "a"])(None, None,
      ...                                       {"a": 42, "b": [1, 2, 3]})
      'b=[1, 2, 3] a=42'

.. autoclass:: LogfmtRenderer

   .. doctest::

      >>> from structlog.processors import LogfmtRenderer
      >>> event_dict = {"a": 42, "b": [1, 2, 3], "flag": True}
      >>> LogfmtRenderer(sort_keys=True)(None, None, event_dict)
      'a=42 b="[1, 2, 3]" flag'
      >>> LogfmtRenderer(key_order=["b", "a"], bool_as_flag=False)(None, None, event_dict)
      'b="[1, 2, 3]" a=42 flag=true'

.. autoclass:: EventRenamer

.. autofunction:: add_log_level

.. autoclass:: UnicodeDecoder

.. autoclass:: UnicodeEncoder

.. autoclass:: ExceptionRenderer

.. autofunction:: format_exc_info

   .. doctest::

      >>> from structlog.processors import format_exc_info
      >>> try:
      ...     raise ValueError
      ... except ValueError:
      ...     format_exc_info(None, None, {"exc_info": True})  # doctest: +ELLIPSIS
      {'exception': 'Traceback (most recent call last):...

.. autofunction:: dict_tracebacks

   .. doctest::

      >>> from structlog.processors import dict_tracebacks
      >>> try:
      ...     raise ValueError("onoes")
      ... except ValueError:
      ...     dict_tracebacks(None, None, {"exc_info": True})  # doctest: +ELLIPSIS
      {'exception': [{'exc_type': 'ValueError', 'exc_value': 'onoes', ..., 'frames': [{'filename': ...

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

.. autoclass:: CallsiteParameter
   :members:

.. autoclass:: CallsiteParameterAdder


`structlog.stdlib` Module
-------------------------

.. automodule:: structlog.stdlib

.. autofunction:: recreate_defaults

.. autofunction:: get_logger

.. autoclass:: BoundLogger
   :members: bind, unbind, try_unbind, new, debug, info, warning, warn, error, critical, exception, log, adebug, ainfo, awarning, aerror, acritical, aexception, alog

.. autoclass:: AsyncBoundLogger

.. autoclass:: LoggerFactory
   :members: __call__

.. autofunction:: render_to_log_kwargs

.. autofunction:: filter_by_level

.. autofunction:: add_log_level

.. autofunction:: add_log_level_number

.. autofunction:: add_logger_name

.. autofunction:: ExtraAdder

.. autoclass:: PositionalArgumentsFormatter

.. autoclass:: ProcessorFormatter
   :members: wrap_for_formatter, remove_processors_meta


`structlog.tracebacks` Module
-----------------------------

.. automodule:: structlog.tracebacks

.. autofunction:: extract
.. autoclass:: ExceptionDictTransformer
.. autoclass:: Trace
.. autoclass:: Stack
.. autoclass:: Frame
.. autoclass:: SyntaxError_


`structlog.typing` Module
-------------------------

.. automodule:: structlog.typing

.. autoclass:: BindableLogger

   Additionally to the methods listed below, bound loggers **must** have a ``__init__`` method with the following signature:

   .. method:: __init__(self, wrapped_logger: WrappedLogger, processors: Iterable[Processor], context: Context) -> None
      :noindex:

   Unfortunately it's impossible to define initializers using :pep:`544` Protocols.

   They currently also have to carry a `Context` as a ``_context`` attribute.

   .. note::

     Currently Sphinx has no support for Protocols, so please click ``[source]`` for this entry to see the full definition.

.. autoclass:: FilteringBoundLogger

   .. note::

     Currently Sphinx has no support for Protocols, so please click ``[source]`` for this entry to see the full definition.

.. autoclass:: ExceptionTransformer

   .. note::

     Currently Sphinx has no support for Protocols, so please click ``[source]`` for this entry to see the full definition.

.. autodata:: EventDict
.. autodata:: WrappedLogger
.. autodata:: Processor
.. autodata:: Context
.. autodata:: ExcInfo
.. autodata:: ExceptionRenderer


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
