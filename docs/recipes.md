# Recipes

Thanks to the fact that *structlog* is entirely based on dictionaries and callables, the sky is the limit with what you an achieve.
In the beginning that can be daunting, so here are a few examples of tasks that have come up repeatedly.

Please note that recipes related to integration with frameworks have an [own chapter](frameworks.md).

(rename-event)=

## Renaming the `event` Key

The name of the event is hard-coded in *structlog* to `event`.
But that doesn't mean it has to be called that in your logs.

With the {class}`structlog.processors.EventRenamer` processor you can for instance rename  the log message to `msg` and use `event` for something custom, that you bind to `_event` in your code:

```pycon
>>> from structlog.processors import EventRenamer
>>> event_dict = {"event": "something happened", "_event": "our event!"}
>>> EventRenamer("msg", "_event")(None, None, event_dict)
{'msg': 'something happened', 'event': 'our event!'}
```

(finer-filtering)=

## Fine-Grained Log-Level Filtering

*structlog*'s native log levels as provided by {func}`structlog.make_filtering_bound_logger` only know **one** log level – the one that is passed to `make_filtering_bound_logger()`.
Sometimes it can be useful to filter more strictly for certain modules or even functions.

You can achieve that with by adding the {class}`~structlog.processors.CallsiteParameterAdder` processor and writing a simple own one that acts on the data you get:

Let's assume you have the following code:

```python
logger = structlog.get_logger()

def f():
    logger.info("f called")

def g():
    logger.info("g called")

f()
g()
```

And you don't want to see log entries from function `f`.
You add {class}`~structlog.processors.CallsiteParameterAdder` to the processor chain and then look at the `func_name` field in the *event dict*:

```python
def filter_f(_, __, event_dict):
    if event_dict.get("func_name") == "f":
        raise structlog.DropEvent

    return event_dict

structlog.configure(
    processors=[
        structlog.processors.CallsiteParameterAdder(
            [structlog.processors.CallsiteParameter.FUNC_NAME]
        ),
        filter_f,  # <-- your processor!
        structlog.processors.KeyValueRenderer(),
    ]
)
```

Running this gives you:

```
event='g called' func_name='g'
```

{class}`~structlog.processors.CallsiteParameterAdder` is *very* powerful in what info it can add, so your possibilities are limitless.
Pick the data you're interested in from the {class}`structlog.processors.CallsiteParameter` {class}`~enum.Enum`.


(custom-wrappers)=

## Custom Wrappers

```{eval-rst}
.. testsetup:: *

   import structlog
   structlog.configure(
       processors=[structlog.processors.KeyValueRenderer()],
   )
```

```{eval-rst}
.. testcleanup:: *

   import structlog
   structlog.reset_defaults()

```

The type of the *bound loggers* that are returned by {func}`structlog.get_logger()` is called the *wrapper class*, because it wraps the original logger that takes care of the output.
This wrapper class is [configurable](configuration.md).

Originally, *structlog* used a generic wrapper class {class}`structlog.BoundLogger` by default.
That class still ships with *structlog* and can wrap *any* logger class by intercepting unknown method names and proxying them to the wrapped logger.

Nowadays, the default is a {class}`structlog.typing.FilteringBoundLogger` that imitates standard library’s log levels with the possibility of efficiently filtering at a certain level (inactive log methods are a plain `return None` each).

If you’re integrating with {mod}`logging` or Twisted, you may was to use one of their specific *bound loggers* ({class}`structlog.stdlib.BoundLogger` and {class}`structlog.twisted.BoundLogger`, respectively).

—

On top of that all, you can also write your own wrapper classes.
To make it easy for you, *structlog* comes with the class {class}`structlog.BoundLoggerBase` which takes care of all data binding duties so you just add your log methods if you choose to sub-class it.

(wrapper-class-example)=

### Example

It’s easiest to demonstrate with an example:

```{eval-rst}
.. doctest::

   >>> from structlog import BoundLoggerBase, PrintLogger, wrap_logger
   >>> class SemanticLogger(BoundLoggerBase):
   ...    def info(self, event, **kw):
   ...        if not "status" in kw:
   ...            return self._proxy_to_logger("info", event, status="ok", **kw)
   ...        else:
   ...            return self._proxy_to_logger("info", event, **kw)
   ...
   ...    def user_error(self, event, **kw):
   ...        self.info(event, status="user_error", **kw)
   >>> log = wrap_logger(PrintLogger(), wrapper_class=SemanticLogger)
   >>> log = log.bind(user="fprefect")
   >>> log.user_error("user.forgot_towel")
   user='fprefect' status='user_error' event='user.forgot_towel'
```

You can observe the following:

- The wrapped logger can be found in the instance variable {attr}`structlog.BoundLoggerBase._logger`.
- The helper method {meth}`structlog.BoundLoggerBase._proxy_to_logger` that is a [DRY] convenience function that runs the processor chain, handles possible {class}`structlog.DropEvent`s and calls a named function on `_logger`.
- You can run the chain by hand through using {meth}`structlog.BoundLoggerBase._process_event` .

These two methods and one attribute are all you need to write own *bound loggers*.

[dry]: https://en.wikipedia.org/wiki/Don%27t_repeat_yourself
