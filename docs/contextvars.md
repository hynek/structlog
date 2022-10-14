(contextvars)=

# Context Variables

```{eval-rst}
.. testsetup:: *

   import structlog
```

```{eval-rst}
.. testcleanup:: *

   import structlog
   structlog.reset_defaults()
```

The {mod}`contextvars` module in the Python standard library allows having a global `structlog` context that is local to the current execution context.
The execution context can be thread-local if using threads, or using primitives based on {mod}`asyncio`, or [*greenlet*](https://greenlet.readthedocs.io/) respectively.

For example, you may want to bind certain values like a request ID or the peer's IP address at the beginning of a web request and have them logged out along with the local contexts you build within our views.

For that `structlog` provides the {mod}`structlog.contextvars` module with a set of functions to bind variables to a context-local context.
This context is safe to be used both in threaded as well as asynchronous code.

The general flow is:

- Use {func}`structlog.configure` with {func}`structlog.contextvars.merge_contextvars` as your first processor (part of default configuration).
- Call {func}`structlog.contextvars.clear_contextvars` at the beginning of your request handler (or whenever you want to reset the context-local context).
- Call {func}`structlog.contextvars.bind_contextvars` and {func}`structlog.contextvars.unbind_contextvars` instead of your bound logger's `bind()` and `unbind()` when you want to bind and unbind key-value pairs to the context-local context.
  You can also use the {func}`structlog.contextvars.bound_contextvars` context manager / decorator.
- Use `structlog` as normal.
  Loggers act as they always do, but the {func}`structlog.contextvars.merge_contextvars` processor ensures that any context-local binds get included in all of your log messages.
- If you want to access the context-local storage, you use {func}`structlog.contextvars.get_contextvars` and {func}`structlog.contextvars.get_merged_contextvars`.

We're sorry the word *context* means three different things in this itemization depending on ... context.

```{eval-rst}
.. doctest::

   >>> from structlog.contextvars import (
   ...     bind_contextvars,
   ...     bound_contextvars,
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
   >>> # middleware), clear the contextvars-local context and bind some common
   >>> # values:
   >>> clear_contextvars()
   >>> bind_contextvars(a=1, b=2)
   {'a': <Token var=<ContextVar name='structlog_a' default=Ellipsis at ...> at ...>, 'b': <Token var=<ContextVar name='structlog_b' default=Ellipsis at ...> at ...>}
   >>> # Then use loggers as per normal
   >>> # (perhaps by using structlog.get_logger() to create them).
   >>> log.info("hello")
   event='hello' a=1 b=2
   >>> # Use unbind_contextvars to remove a variable from the context.
   >>> unbind_contextvars("b")
   >>> log.info("world")
   event='world' a=1
   >>> # You can also bind key-value pairs temporarily.
   >>> with bound_contextvars(b=2):
   ...    log.info("hi")
   event='hi' a=1 b=2
   >>> # Now it's gone again.
   >>> log.info("hi")
   event='hi' a=1
   >>> # And when we clear the contextvars state again, it goes away.
   >>> # a=None is printed due to the key_order argument passed to
   >>> # KeyValueRenderer, but it is NOT present anymore.
   >>> clear_contextvars()
   >>> log.info("hi there")
   event='hi there' a=None
```


## Support for `contextvars.Token`

If e.g. your request handler calls a helper function that needs to temporarily override some contextvars before restoring them back to their original values, you can use the {class}`~contextvars.Token`s returned by {func}`~structlog.contextvars.bind_contextvars` along with {func}`~structlog.contextvars.reset_contextvars` to accomplish this (much like how {meth}`contextvars.ContextVar.reset` works):

```python
def foo():
    bind_contextvars(a=1)
    _helper()
    log.info("a is restored!")  # a=1

def _helper():
    tokens = bind_contextvars(a=2)
    log.info("a is overridden")  # a=2
    reset_contextvars(**tokens)
```

(flask-example)=

## Example: Flask and Thread-Local Data

Let's assume you want to bind a unique request ID, the URL path, and the peer's IP to every log entry by storing it in thread-local storage that is managed by context variables:

```python
import logging
import sys
import uuid

import flask

from .some_module import some_function

import structlog

logger = structlog.get_logger()
app = flask.Flask(__name__)

@app.route("/login", methods=["POST", "GET"])
def some_route():
    # You would put this into some kind of middleware or processor so it's set
    # automatically for all requests in all views.
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        view=flask.request.path,
        request_id=str(uuid.uuid4()),
        peer=flask.request.access_route[0],
    )
    # End of belongs-to-middleware.

    log = logger.bind()
    # do something
    # ...
    log.info("user logged in", user="test-user")
    # ...
    some_function()
    # ...
    return "logged in!"


if __name__ == "__main__":
    logging.basicConfig(
        format="%(message)s", stream=sys.stdout, level=logging.INFO
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,  # <--!!!
            structlog.processors.KeyValueRenderer(
                key_order=["event", "view", "peer"]
            ),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    app.run()

```

`some_module.py`:

```python
from structlog import get_logger

logger = get_logger()

def some_function():
    # ...
    logger.error("user did something", something="shot_in_foot")
    # ...
```

This would result among other the following lines to be printed:

```text
event='user logged in' view='/login' peer='127.0.0.1' user='test-user' request_id='e08ddf0d-23a5-47ce-b20e-73ab8877d736'
event='user did something' view='/login' peer='127.0.0.1' something='shot_in_foot' request_id='e08ddf0d-23a5-47ce-b20e-73ab8877d736'
```

As you can see, `view`, `peer`, and `request_id` are present in **both** log entries.
