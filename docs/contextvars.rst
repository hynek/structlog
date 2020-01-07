.. _contextvars:

contextvars
===========

.. testsetup:: *

   import structlog

.. testcleanup:: *

   import structlog
   structlog.reset_defaults()

Historically, ``structlog`` only supported thread-local context binding.
With the introduction of ``contextvars`` in Python 3.7, there is now a way of having a global context that is local to the current context and even works in concurrent code.

The ``merge_context_local`` Processor
-------------------------------------

``structlog`` provides a set of functions to bind variables to a context-local context.
This context is safe to be used in asynchronous code.
The functions are:

- :func:`structlog.contextvars.merge_context_local`,
- :func:`structlog.contextvars.clear_context_local`,
- :func:`structlog.contextvars.bind_context_local`,
- :func:`structlog.contextvars.unbind_context_local`,

The general flow of using these functions is:

- Use :func:`structlog.configure` with :func:`structlog.contextvars.merge_context_local` as your first processor.
- Call :func:`structlog.contextvars.clear_context_local` at the beginning of your request handler (or whenever you want to reset the context-local context).
- Call :func:`structlog.contextvars.bind_context_local` and :func:`structlog.contextvars.unbind_context_local` instead of :func:`structlog.BoundLogger.bind` and :func:`structlog.BoundLogger.unbind` when you want to (un)bind a particular variable to the context-local context.
- Use ``structlog`` as normal.
  Loggers act as the always do, but the :func:`structlog.contextvars.merge_context_local` processor ensures that any context-local binds get included in all of your log messages.

.. doctest::

   >>> from structlog.contextvars import (
   ...     bind_context_local,
   ...     clear_context_local,
   ...     merge_context_local,
   ...     unbind_context_local,
   ... )
   >>> from structlog import configure
   >>> configure(
   ...     processors=[
   ...         merge_context_local,
   ...         structlog.processors.KeyValueRenderer(),
   ...     ]
   ... )
   >>> log = structlog.get_logger()
   >>> # At the top of your request handler (or, ideally, some general
   >>> # middleware), clear the threadlocal context and bind some common
   >>> # values:
   >>> clear_context_local()
   >>> bind_context_local(a=1, b=2)
   >>> # Then use loggers as per normal
   >>> # (perhaps by using structlog.get_logger() to create them).
   >>> log.msg("hello")
   a=1 b=2 event='hello'
   >>> # Use unbind_context_local to remove a variable from the context
   >>> unbind_context_local("b")
   >>> log.msg("world")
   a=1 event='world'
   >>> # And when we clear the threadlocal state again, it goes away.
   >>> clear_context_local()
   >>> log.msg("hi there")
   event='hi there'
