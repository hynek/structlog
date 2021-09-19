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

For that ``structlog`` provides the `structlog.contextvars` module with a set of functions to bind variables to a context-local context.
This context is safe to be used in asynchronous code.

The general flow is:

- Use `structlog.configure` with `structlog.contextvars.merge_contextvars` as your first processor.
- Call `structlog.contextvars.clear_contextvars` at the beginning of your request handler (or whenever you want to reset the context-local context).
- Call `structlog.contextvars.bind_contextvars` and `structlog.contextvars.unbind_contextvars` instead of your bound logger's ``bind()`` and ``unbind()`` when you want to bind and unbind key-value pairs to the context-local context.
- Use ``structlog`` as normal.
  Loggers act as they always do, but the `structlog.contextvars.merge_contextvars` processor ensures that any context-local binds get included in all of your log messages.

.. doctest::

   >>> from structlog.contextvars import (
   ...     bind_contextvars,
   ...     clear_contextvars,
   ...     merge_contextvars,
   ...     unbind_contextvars,
   ... )
   >>> from structlog import configure
   >>> configure(
   ...     processors=[
   ...         merge_contextvars,
   ...         structlog.processors.KeyValueRenderer(key_order=["event", "a"]),
   ...     ]
   ... )
   >>> log = structlog.get_logger()
   >>> # At the top of your request handler (or, ideally, some general
   >>> # middleware), clear the threadlocal context and bind some common
   >>> # values:
   >>> clear_contextvars()
   >>> bind_contextvars(a=1, b=2)
   {'a': <Token var=<ContextVar name='structlog_a' default=Ellipsis at ...> at ...>, 'b': <Token var=<ContextVar name='structlog_b' default=Ellipsis at ...> at ...>}
   >>> # Then use loggers as per normal
   >>> # (perhaps by using structlog.get_logger() to create them).
   >>> log.msg("hello")
   event='hello' a=1 b=2
   >>> # Use unbind_contextvars to remove a variable from the context
   >>> unbind_contextvars("b")
   >>> log.msg("world")
   event='world' a=1
   >>> # And when we clear the threadlocal state again, it goes away.
   >>> # a=None is printed due to the key_order argument passed to
   >>> # KeyValueRenderer, but it is NOT present anymore.
   >>> clear_contextvars()
   >>> log.msg("hi there")
   event='hi there' a=None


If e.g. your request handler calls a helper function that needs to temporarily override some contextvars before restoring them back to their original values, you can use the :class:`~contextvars.contextvars.Token`\s returned by :func:`~structlog.contextvars.bind_contextvars` along with :func:`~structlog.contextvars.reset_contextvars` to accomplish this (much like how :meth:`contextvars.ContextVar.reset` works):

.. code-block:: python

    def foo():
        bind_contextvars(a=1)
        _helper()
        log.msg("a is restored!")  # a=1

    def _helper():
        tokens = bind_contextvars(a=2)
        log.msg("a is overridden")  # a=2
        reset_contextvars(**tokens)
