.. _contextvars:

Context Variables
=================

.. testsetup:: *

   import structlog

.. testcleanup:: *

   import structlog
   structlog.reset_defaults()

Historically, ``structlog`` only supported thread-local context binding.
With the introduction of :mod:`contextvars` in Python 3.7, there is now a way of having a global context that is local to the current context and even works in concurrent code such as code using :mod:`asyncio`.

For that ``structlog`` provides a set of functions to bind variables to a context-local context.
This context is safe to be used in asynchronous code.
The functions are:

- :func:`structlog.contextvars.merge_contextvars_context`,
- :func:`structlog.contextvars.clear_contextvars`,
- :func:`structlog.contextvars.bind_contextvars`,
- :func:`structlog.contextvars.unbind_contextvars`,

The general flow of using these functions is:

- Use :func:`structlog.configure` with :func:`structlog.contextvars.merge_contextvars_context` as your first processor.
- Call :func:`structlog.contextvars.clear_contextvars` at the beginning of your request handler (or whenever you want to reset the context-local context).
- Call :func:`structlog.contextvars.bind_contextvars` and :func:`structlog.contextvars.unbind_contextvars` instead of :func:`structlog.BoundLogger.bind` and :func:`structlog.BoundLogger.unbind` when you want to (un)bind a particular variable to the context-local context.
- Use ``structlog`` as normal.
  Loggers act as the always do, but the :func:`structlog.contextvars.merge_contextvars_context` processor ensures that any context-local binds get included in all of your log messages.

.. doctest::

   >>> from structlog.contextvars import (
   ...     bind_contextvars,
   ...     clear_contextvars,
   ...     merge_contextvars_context,
   ...     unbind_contextvars,
   ... )
   >>> from structlog import configure
   >>> configure(
   ...     processors=[
   ...         merge_contextvars_context,
   ...         structlog.processors.KeyValueRenderer(),
   ...     ]
   ... )
   >>> log = structlog.get_logger()
   >>> # At the top of your request handler (or, ideally, some general
   >>> # middleware), clear the threadlocal context and bind some common
   >>> # values:
   >>> clear_contextvars()
   >>> bind_contextvars(a=1, b=2)
   >>> # Then use loggers as per normal
   >>> # (perhaps by using structlog.get_logger() to create them).
   >>> log.msg("hello")
   a=1 b=2 event='hello'
   >>> # Use unbind_contextvars to remove a variable from the context
   >>> unbind_contextvars("b")
   >>> log.msg("world")
   a=1 event='world'
   >>> # And when we clear the threadlocal state again, it goes away.
   >>> clear_contextvars()
   >>> log.msg("hi there")
   event='hi there'
