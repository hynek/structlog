# Bound Loggers

The centerpiece of `structlog` that you will interact with most is called a *bound logger*.
It is what you get back from {func}`structlog.get_logger()` and call your logging methods on.

It consists of three parts:

```{image} _static/BoundLogger.svg
```

1. A *context dictionary* that you can *bind* key / value pairs to.
   This dictionary is *merged* into each log entry that is logged from *this logger specifically*.
   That means that every logger has it own context, but it is possible to have global contexts using {doc}`context variables <contextvars>`.
2. A list of {doc}`processors <processors>` that are called on every log entry.
   Each processor receives the return value of its predecessor passed as an argument.
3. And finally a *logger* that it's wrapping.
   This wrapped logger is responsible for the *output* of the log entry that has been returned by the last processor.
   This *can* be standard library's {class}`logging.Logger`, but absolutely doesn't have to:
   By default it's `structlog`'s {class}`structlog.PrintLogger`.

:::{important}
Bound loggers themselves do *not* do any I/O themselves.

All they do is managing the *context* and proxying log calls to a *wrapped logger*.
:::

To manipulate the context dictionary, a *bound logger* offers to:

- Recreate itself with (optional) *additional* context data: {func}`~structlog.BoundLoggerBase.bind` and {func}`~structlog.BoundLoggerBase.new`.
- Recreate itself with *less* context data: {func}`~structlog.BoundLoggerBase.unbind` and {func}`~structlog.BoundLoggerBase.try_unbind`.

In any case, the original bound logger or its context are never mutated.

---

Finally, if you call *any other* method on {class}`~structlog.BoundLogger`, it will:

1. Make a copy of the context -- now it becomes the *event dictionary*,
2. Add the keyword arguments of the method call to the event dict.
3. Add a new key `event` with the value of the first positional argument of the method call to the event dict.
4. Run the processors successively on the event dict.
   Each processor receives the result of its predecessor.
5. Finally, it takes the result of the final processor and calls the method with the same name – that got called on the bound logger – on the wrapped logger[^explicit].
   For flexibility, the final processor can return either a string[^str] that is passed directly as a positional parameter, or a tuple `(args, kwargs)` that are passed as `wrapped_logger.log_method(*args, **kwargs)`.

[^explicit]: Since this is slightly magical, `structlog` comes with concrete loggers for the `standard-library` and {doc}`twisted` that offer you explicit APIs for the supported logging methods but behave identically like the generic BoundLogger otherwise.
    Of course, you are free to implement your own bound loggers too.

[^str]: `str`, `bytes`, or `bytearray` to be exact.


## Wrapping Loggers Explicitly

In practice, you won't be instantiating bound loggers yourself.
You will configure `structlog` as explained in the {doc}`next chapter <configuration>` and then just call {func}`structlog.get_logger`.

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
