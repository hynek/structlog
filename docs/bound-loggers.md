# Bound Loggers

The centerpiece of *structlog* that you will interact with most is called a *bound logger*.

It's what you get back from {func}`structlog.get_logger()` and it's called a *bound logger* because you can *bind* key-value pairs to it.

As far as *structlog* is concerned, it consists of three parts:

```{image} _static/BoundLogger.svg
```

1. A *context dictionary* that you can *bind* key-value pairs to.
   This dictionary is *merged* into each log entry that is logged from *this logger specifically*.

   You can inspect a context of a *bound logger* by calling {func}`structlog.get_context()` on it.
2. A list of {doc}`processors <processors>` that are called on every log entry.
   Each processor receives the return value of its predecessor passed as an argument.

   This list is usually set using {doc}`configuration`.
3. And finally a *logger* that it's wrapping.
   This wrapped logger is responsible for the *output* of the log entry that has been returned by the last processor.
   This *can* be standard library's {class}`logging.Logger` like in the image above, but absolutely doesn't have to:
   By default it's *structlog*'s {class}`~structlog.PrintLogger`.

   This wrapped logger also is usually set using {doc}`configuration`.

:::{important}
Bound loggers themselves do *not* do any I/O themselves.

All they do is manage the *context* and proxy log calls to a *wrapped logger*.
:::


## Context

To manipulate the context dictionary, a *bound logger* can:

- Recreate itself with (optional) *additional* context data: {func}`~structlog.BoundLoggerBase.bind` and {func}`~structlog.BoundLoggerBase.new`.
- Recreate itself with *less* context data: {func}`~structlog.BoundLoggerBase.unbind` and {func}`~structlog.BoundLoggerBase.try_unbind`.

In any case, the original bound logger or its context are never mutated.
They always return a *copy* of the bound logger with a *new* context that reflects your changes.

This part of the API is defined in the {class}`typing.Protocol` called {class}`structlog.typing.BindableLogger`.
The protocol is marked {func}`typing.runtime_checkable` which means that you can check an object for being a *bound logger* using `isinstance(obj, structlog.typing.BindableLogger)`.


## Output

Finally, a *bound logger* also **indirectly** exposes the logging methods of the *wrapped logger*.
By default, that's a {class}`~structlog.typing.FilteringBoundLogger` that is wrapping a {class}`~structlog.PrintLogger`.
They both share the set of log methods that's present in the standard library: `debug()`, `info()`, `warning()`, `error()`, and `critical()`.

Whenever you call one of those methods on the *bound logger*, it will:

1. Make a copy of its context -- now it becomes the *event dictionary*,
2. Add the keyword arguments of the method call to the event dict.
3. Add a new key `event` with the value of the first positional argument of the method call to the event dict.
4. Run the processors successively on the event dict.
   Each processor receives the result of its predecessor.
5. Finally, it takes the result of the final processor and calls the method with the same name – that got called on the *bound logger* – on the wrapped logger.

   For flexibility, the final processor can return either a string[^str] that is passed directly as a positional parameter, or a tuple `(args, kwargs)` that are passed as `wrapped_logger.log_method(*args, **kwargs)`.

[^str]: {any}`str`, {any}`bytes`, or {any}`bytearray` to be exact.


### Step-by-Step Example

Assuming you've left the default configuration and have:

```python
import structlog

logger = structlog.get_logger()

log = logger.bind(foo="bar")
```

Now `log` is a *bound logger* of type {class}`~structlog.typing.FilteringBoundLogger` (but in the default config there's no filtering).
`log`'s context is `{"foo": "bar"}` and its wrapped logger is a {class}`structlog.PrintLogger`.

Now if you call `log.info("Hello, %s!", "world", number=42)` the following happens:

1. `"world"` gets interpolated into `"Hello, %s!"`, making the event "Hello, world!".
2. The *bound logger*'s context gets copied and the key-value pairs from the `info` call are added to it.
   It becomes an *event dict* and is `{"foo": "bar", "number": 42}` now.
3. The event from step 1 is added too.
   The *event dict* is `{"foo": "bar", "number": 42, "event": "Hello, world!"}` now.
4. The *event dict* is fed into the [processor chain](processors.md).
   In this case the processors add a timestamp and the log level name to the *event dict*.

   Before it hits the last processor, the *event dict* looks something like `{"foo": "bar", "number": 42, "event": "Hello, world!", "level": "info", "timestamp": "2022-10-13 16:29:27"}` now.

   The last processor is {class}`structlog.dev.ConsoleRenderer` and renders the *event dict* into a colorful string[^json].
5. Finally, the *wrapped logger*'s (a {class}`~structlog.PrintLogger`) `info()` method is called with that string.

[^json]: Until this very step, the *event dict* was a dictionary.
   By replacing the last processor, you decide on the **format** of your logs.
   For example, if you wanted JSON logs, you just have to replace the last processor with {class}`structlog.processors.JSONRenderer`.


(filtering)=

## Filtering by Log Levels

Filtering based on log levels can be done in a processor very easily[^stdlib], however that means unnecessary performance overhead through function calls.
We care a lot about performance and that's why *structlog*'s default *bound logger* class implements level-filtering as close to the users as possible: in the *bound logger*'s logging methods *before* even creating an *event dict* and starting the processor chain.

{func}`structlog.make_filtering_bound_logger` allows you to create a *bound logger* whose log methods with a log level beneath the configured one consist of a plain `return None`.

Here's an example:

```pycon
>>> import structlog
>>> logger = structlog.get_logger()
>>> logger.debug("hi!")
2022-10-15 11:39:03 [debug    ] hi!
>>> import logging
>>> structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))
>>> logger.debug("hi!")
# no output!
```

In this example, we first log out using the default logger that doesn't filter at all.
Then we change the configuration to filtering at the info level and try again:
no log output!

Let's have a look at the `debug` method:

```pycon
>>> import inspect
>>> print(inspect.getsource(logger.debug))
def _nop(self: Any, event: str, **kw: Any) -> Any:
    return None
```

This is as effective as it gets and usually as flexible as the vast majority of users need.

:::{important}
*structlog* uses the constants from {mod}`logging`, but does **not** share any code.
Passing `20` instead of `logging.INFO` would have worked too.
:::

[^stdlib]: And it's in fact supported for standard library logging with the {func}`structlog.stdlib.filter_by_level` processor.


## Wrapping Loggers Manually

In practice, you won't be instantiating bound loggers yourself.
You will configure *structlog* as explained in the {doc}`next chapter <configuration>` and then just call {func}`structlog.get_logger`.

However, in some rare cases you may not want to do that.
For example because you don't control how you get the logger that you would like to wrap (famous example: *Celery*).
For that times there is the {func}`structlog.wrap_logger` function that can be used to wrap a logger -- optionally without any global state (i.e. configuration):

(proc)=

```{eval-rst}
.. doctest::

   >>> import structlog
   >>> class CustomPrintLogger:
   ...     def msg(self, message):
   ...         print(message)
   >>> def proc(logger, method_name, event_dict):
   ...     print("I got called with", event_dict)
   ...     return repr(event_dict)
   >>> log = structlog.wrap_logger(
   ...     CustomPrintLogger(),
   ...     wrapper_class=structlog.BoundLogger,
   ...     processors=[proc],
   ... )
   >>> log2 = log.bind(x=42)
   >>> log == log2
   False
   >>> log.msg("hello world")
   I got called with {'event': 'hello world'}
   {'event': 'hello world'}
   >>> log2.msg("hello world")
   I got called with {'x': 42, 'event': 'hello world'}
   {'x': 42, 'event': 'hello world'}
   >>> log3 = log2.unbind("x")
   >>> log == log3
   True
   >>> log3.msg("nothing bound anymore", foo="but you can structure the event too")
   I got called with {'foo': 'but you can structure the event too', 'event': 'nothing bound anymore'}
   {'foo': 'but you can structure the event too', 'event': 'nothing bound anymore'}
```
