Processors
==========

The true power of ``structlog`` lies in its *composable log processors*.
You can define a chain of callables that will get passed the wrapped logger, the name of the wrapped method, and the current context together with the current event (called ``event_dict``) as positional arguments.
The return value of each processor is passed on to the next one as ``event_dict`` until finally the return value of the last processor gets passed into the wrapped logging method.
Therefore, the last processor must adapt the ``event_dict`` into something the underlying logging method understands.

There are two special return values:

- ``False`` aborts the processor chain and the log entry is silently dropped.
- ``None`` raises an ``ValueError`` because you probably forgot to return a new value.

Additionally, the last processor can either return a string that is passed as the first (and only) positional argument to the underlying logger or a tuple of ``(args, kwargs)`` that are passed as ``log_method(*args, **kwargs)``.
Therefore ``return 'hello world'`` is a shortcut for ``return (('hello world',), {})``.

This should give you enough power to use it with any logging system.
