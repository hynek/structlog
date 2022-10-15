# Standard Library Logging

Ideally, `structlog` should be able to be used as a drop-in replacement for standard library's {mod}`logging` by wrapping it.
In other words, you should be able to replace your call to {func}`logging.getLogger` by a call to {func}`structlog.get_logger` and things should keep working as before (if `structlog` is configured right, see {ref}`stdlib-config` below).

If you run into incompatibilities, it is a *bug* so please take the time to [report it](https://github.com/hynek/structlog/issues)!
If you're a heavy `logging` user, your [help](https://github.com/hynek/structlog/issues?q=is%3Aopen+is%3Aissue+label%3Astdlib) to ensure a better compatibility would be highly appreciated!

:::{note}
The quickest way to get started with `structlog` and `logging` is {func}`structlog.stdlib.recreate_defaults()` that will recreate the default configuration on top of `logging` and optionally configure `logging` for you.
:::


## Just Enough `logging`

If you want to use `structlog` with `logging`, you should have at least a fleeting understanding on how the standard library operates because `structlog` will *not* do any magic things in the background for you.
Most importantly you have to *configure* the `logging` system *additionally* to configuring `structlog`.

Usually it is enough to use:

```
import logging
import sys

logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)
```

This will send all log messages with the [log level](https://docs.python.org/3/library/logging.html#logging-levels) `logging.INFO` and above (that means that e.g. `logging.debug` calls are ignored) to standard out without any special formatting by the standard library.

If you require more complex behavior, please refer to the standard library's `logging` documentation.


## Concrete Bound Logger

`structlog` ships a stdlib-specific [*bound logger*](bound-loggers.md) that  mirrors the log methods of standard library's {any}`logging.Logger` with correct type hints.

If you want to take advantage of said type hints, you have to either annotate the logger coming from {func}`structlog.get_logger`, or use {func}`structlog.stdlib.get_logger()` that has the appropriate type hints.
Please note though, that it will neither configure nor verify your configuration.
It will call `structlog.get_logger()` just like if you would've called it -- the only difference are the type hints.

See also {doc}`types`.


### `asyncio`

For `asyncio` applications, you may not want your whole application to block while your processor chain is formatting your log entries.
For that use case `structlog` comes with {class}`structlog.stdlib.AsyncBoundLogger` that will do all processing in a thread pool executor.

This means an increased computational cost per log entry but your application will never block because of logging.

To use it, {doc}`configure <configuration>` `structlog` to use `AsyncBoundLogger` as `wrapper_class`.


## Processors

`structlog` comes with a few standard library-specific processors:

{func}`~structlog.stdlib.render_to_log_kwargs`:

: Renders the event dictionary into keyword arguments for `logging.log` that attaches everything except the `event` field to the *extra* argument.
  This is useful if you want to render your log entries entirely within `logging`.

{func}`~structlog.stdlib.filter_by_level`:

: Checks the log entry's log level against the configuration of standard library's logging.
  Log entries below the threshold get silently dropped.
  Put it at the beginning of your processing chain to avoid expensive operations from happening in the first place.

{func}`~structlog.stdlib.add_logger_name`:

: Adds the name of the logger to the event dictionary under the key `logger`.

{func}`~structlog.stdlib.ExtraAdder`:

: Add extra attributes of `logging.LogRecord` objects to the event dictionary.

  This processor can be used for adding data passed in the `extra` parameter of the `logging` module's log methods to the event dictionary.

{func}`~structlog.stdlib.add_log_level`:

: Adds the log level to the event dictionary under the key `level`.

{func}`~structlog.stdlib.add_log_level_number`:

: Adds the log level number to the event dictionary under the key `level_number`.
  Log level numbers map to the log level names.
  The Python stdlib uses them for filtering logic.
  This adds the same numbers so users can leverage similar filtering.
  Compare:

  ```
  level in ("warning", "error", "critical")
  level_number >= 30
  ```

  The mapping of names to numbers is in `structlog.stdlib._NAME_TO_LEVEL`.

{func}`~structlog.stdlib.PositionalArgumentsFormatter`:

: This processes and formats positional arguments (if any) passed to log methods in the same way the `logging` module would do, e.g. `logger.info("Hello, %s", name)`.

`structlog` also comes with {class}`~structlog.stdlib.ProcessorFormatter` which is a `logging.Formatter` that enables you to format non-`structlog` log entries using `structlog` renderers *and* multiplex `structlog`’s output with different renderers (see [below](processor-formatter) for an example).

(stdlib-config)=

## Suggested Configurations

:::{note}
We do appreciate that fully integrating `structlog` with standard library's `logging` is fiddly when done for the first time.

This is the price of flexibility and unfortunately -- given the different needs of our users -- we can't make it any simpler without compromising someone's use-cases.
However, once it is set up, you can rely on not having to ever touch it again.
:::

Depending *where* you'd like to do your formatting, you can take one of four approaches:


### Don't Integrate

The most straight-forward option is to configure standard library `logging` close enough to what `structlog` is logging and leaving it at that.

Since these are usually log entries from third parties that don't take advantage of `structlog`'s features, this is surprisingly often a perfectly adequate approach.

For instance, if you log JSON in production, configure `logging` to use [*python-json-logger*] to make it print JSON too, and then tweak the configuration to match their outputs.


### Rendering Within `structlog`

This is the simplest approach where `structlog` does all the heavy lifting and passes a fully-formatted string to `logging`.
Chances are, this is all you need.

```{eval-rst}
.. mermaid::
   :align: center

   flowchart TD
      %%{ init: {'theme': 'neutral'} }%%
      User
      structlog
      stdlib[Standard Library\ne.g. logging.StreamHandler]

      User --> |"structlog.get_logger().info('foo')"| structlog
      User --> |"logging.getLogger().info('foo')"| stdlib
      structlog --> |"logging.getLogger().info(#quot;{'event': 'foo'}#quot;)"| stdlib ==> Output

      Output
```

A basic configuration to output structured logs in JSON format looks like this:

```python
import structlog

structlog.configure(
    processors=[
        # If log level is too low, abort pipeline and throw away log entry.
        structlog.stdlib.filter_by_level,
        # Add the name of the logger to event dict.
        structlog.stdlib.add_logger_name,
        # Add log level to event dict.
        structlog.stdlib.add_log_level,
        # Perform %-style formatting.
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Add a timestamp in ISO 8601 format.
        structlog.processors.TimeStamper(fmt="iso"),
        # If the "stack_info" key in the event dict is true, remove it and
        # render the current stack trace in the "stack" key.
        structlog.processors.StackInfoRenderer(),
        # If the "exc_info" key in the event dict is either true or a
        # sys.exc_info() tuple, remove "exc_info" and render the exception
        # with traceback into the "exception" key.
        structlog.processors.format_exc_info,
        # If some value is in bytes, decode it to a unicode str.
        structlog.processors.UnicodeDecoder(),
        # Add callsite parameters.
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
        # Render the final event dict as JSON.
        structlog.processors.JSONRenderer()
    ],
    # `wrapper_class` is the bound logger that you get back from
    # get_logger(). This one imitates the API of `logging.Logger`.
    wrapper_class=structlog.stdlib.BoundLogger,
    # `logger_factory` is used to create wrapped loggers that are used for
    # OUTPUT. This one returns a `logging.Logger`. The final value (a JSON
    # string) from the final processor (`JSONRenderer`) will be passed to
    # the method of the same name as that you've called on the bound logger.
    logger_factory=structlog.stdlib.LoggerFactory(),
    # Effectively freeze configuration after creating the first bound
    # logger.
    cache_logger_on_first_use=True,
)
```

To make your program behave like a proper [*12 Factor App*](https://12factor.net/logs) that outputs only JSON to `stdout`, configure the `logging` module like this:

```
import logging
import sys

logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)
```

In this case *only* your own logs are formatted as JSON:

```pycon
>>> structlog.get_logger("test").warning("hello")
{"event": "hello", "logger": "test", "level": "warning", "timestamp": "2017-03-06T07:39:09.518720Z"}

>>> logging.getLogger("test").warning("hello")
hello
```


### Rendering Using `logging`-based Formatters

You can choose to use `structlog` only for building the event dictionary and leave all formatting -- additionally to the output -- to the standard library.

```{eval-rst}
.. mermaid::
   :align: center

   flowchart TD
      %%{ init: {'theme': 'neutral'} }%%
      User
      structlog
      stdlib[Standard Library\ne.g. logging.StreamHandler]

      User --> |"structlog.get_logger().info('foo', bar=42)"| structlog
      User --> |"logging.getLogger().info('foo')"| stdlib
      structlog --> |"logging.getLogger().info('foo', extra={&quot;bar&quot;: 42})"| stdlib ==> Output

      Output

```

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        # Transform event dict into `logging.Logger` method arguments.
        # "event" becomes "msg" and the rest is passed as a dict in
        # "extra". IMPORTANT: This means that the standard library MUST
        # render "extra" for the context to appear in log entries! See
        # warning below.
        structlog.stdlib.render_to_log_kwargs,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

Now you have the event dict available within each log record.
If you want all your log entries (i.e. also those not from your app/`structlog`) to be formatted as JSON, you can use the [*python-json-logger*] library:

```python
import logging
import sys

from pythonjsonlogger import jsonlogger

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(jsonlogger.JsonFormatter())
root_logger = logging.getLogger()
root_logger.addHandler(handler)
```

Now both `structlog` and `logging` will emit JSON logs:

```pycon
>>> structlog.get_logger("test").warning("hello")
{"message": "hello", "logger": "test", "level": "warning"}

>>> logging.getLogger("test").warning("hello")
{"message": "hello"}
```

:::{warning}
With this approach, it's the standard library `logging` formatter's duty to do something useful with the event dict.
In the above example that's `jsonlogger.JsonFormatter`.

Keep this in mind if you only get the event name without any context, and exceptions are ostensibly swallowed.
:::

(processor-formatter)=

### Rendering Using `structlog`-based Formatters Within `logging`

Finally, the most ambitious approach.
Here, you use `structlog`'s {class}`~structlog.stdlib.ProcessorFormatter` as a {any}`logging.Formatter` for both `logging` as well as `structlog` log entries.

Consequently, the output is the duty of the standard library too.

```{eval-rst}
.. mermaid::
   :align: center

   flowchart TD
      %%{ init: {'theme': 'neutral'} }%%
      User
      structlog
      structlog2[structlog]
      stdlib["Standard Library"]

      User --> |"structlog.get_logger().info(#quot;foo#quot;, bar=42)"| structlog
      User --> |"logging.getLogger().info(#quot;foo#quot;)"| stdlib
      structlog --> |"logging.getLogger().info(event_dict, {#quot;extra#quot;: {#quot;_logger#quot;: logger, #quot;_name#quot;: name})"| stdlib

      stdlib --> |"structlog.stdlib.ProcessorFormatter.format(logging.Record)"| structlog2
      structlog2 --> |"Returns a string that is passed into logging handlers.\nThis flow is controlled by the logging configuration."| stdlib2

      stdlib2[Standard Library\ne.g. logging.StreamHandler] ==> Output

```

{class}`~structlog.stdlib.ProcessorFormatter` has two parts to its API:

1. On the `structlog` side, the {doc}`processor chain <processors>` must be configured to end with {func}`structlog.stdlib.ProcessorFormatter.wrap_for_formatter` as the renderer.
   It converts the processed event dictionary into something that `ProcessorFormatter` understands.

2. On the `logging` side, you must configure `ProcessorFormatter` as your formatter of choice.
   `logging` then calls `ProcessorFormatter`'s `format()` method.

   For that, `ProcessorFormatter` wraps a processor chain that is responsible for rendering your log entries to strings.

Thus, the simplest possible configuration looks like the following:

```python
import logging
import structlog

structlog.configure(
    processors=[
        # Prepare event dict for `ProcessorFormatter`.
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

formatter = structlog.stdlib.ProcessorFormatter(
    processors=[structlog.dev.ConsoleRenderer()],
)

handler = logging.StreamHandler()
# Use OUR `ProcessorFormatter` to format all `logging` entries.
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)
```

which will allow both of these to work in other modules:

```pycon
>>> import logging
>>> import structlog

>>> logging.getLogger("stdlog").info("woo")
woo      _from_structlog=False _record=<LogRecord:...>
>>> structlog.get_logger("structlog").info("amazing", events="oh yes")
amazing  _from_structlog=True _record=<LogRecord:...> events=oh yes
```

Of course, you probably want timestamps and log levels in your output.
The `ProcessorFormatter` has a `foreign_pre_chain` argument which is responsible for adding properties to events from the standard library -- i.e. that do not originate from a `structlog` logger -- and which should in general match the `processors` argument to {func}`structlog.configure` so you get a consistent output.

`_from_structlog` and `_record` allow your processors to determine whether the log entry is coming from `structlog`, and to extract information from `logging.LogRecord`s and add them to the event dictionary.
However, you probably don't want to have them in your log files, thus we've added the `ProcessorFormatter.remove_processors_meta` processor to do so conveniently.

For example, to add timestamps, log levels, and traceback handling to your logs without `_from_structlog` and `_record` noise you should do:

```python
timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
shared_processors = [
    structlog.stdlib.add_log_level,
    timestamper,
]

structlog.configure(
    processors=shared_processors + [
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

formatter = structlog.stdlib.ProcessorFormatter(
    # These run ONLY on `logging` entries that do NOT originate within
    # structlog.
    foreign_pre_chain=shared_processors,
    # These run on ALL entries after the pre_chain is done.
    processors=[
       # Remove _record & _from_structlog.
       structlog.stdlib.ProcessorFormatter.remove_processors_meta,
       structlog.dev.ConsoleRenderer(),
     ],
)
```

which (given the same `logging.*` calls as in the previous example) will result in:

```pycon
>>> logging.getLogger("stdlog").info("woo")
2021-11-15 11:41:47 [info     ] woo
>>> structlog.get_logger("structlog").info("amazing", events="oh yes")
2021-11-15 11:41:47 [info     ] amazing    events=oh yes
```

This allows you to set up some sophisticated logging configurations.
For example, to use the standard library's `logging.config.dictConfig` to log colored logs to the console and plain logs to a file you could do:

```python
import logging.config
import structlog

timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
pre_chain = [
    # Add the log level and a timestamp to the event_dict if the log entry
    # is not from structlog.
    structlog.stdlib.add_log_level,
    # Add extra attributes of LogRecord objects to the event dictionary
    # so that values passed in the extra parameter of log methods pass
    # through to log output.
    structlog.stdlib.ExtraAdder(),
    timestamper,
]

def extract_from_record(_, __, event_dict):
    """
    Extract thread and process names and add them to the event dict.
    """
    record = event_dict["_record"]
    event_dict["thread_name"] = record.threadName
    event_dict["process_name"] = record.processName

    return event_dict

logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                   structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                   structlog.dev.ConsoleRenderer(colors=False),
                ],
                "foreign_pre_chain": pre_chain,
            },
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                   extract_from_record,
                   structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                   structlog.dev.ConsoleRenderer(colors=True),
                ],
                "foreign_pre_chain": pre_chain,
            },
        },
        "handlers": {
            "default": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.handlers.WatchedFileHandler",
                "filename": "test.log",
                "formatter": "plain",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default", "file"],
                "level": "DEBUG",
                "propagate": True,
            },
        }
})
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

This defines two formatters: one plain and one colored.
Both are run for each log entry.
Log entries that do not originate from `structlog`, are additionally pre-processed using a cached `timestamper` and {func}`~structlog.stdlib.add_log_level`.

Additionally, for both `logging` and `structlog` -- but only for the colorful logger -- we also extract some data from {class}`logging.LogRecord`:

```pycon
>>> logging.getLogger().warning("bar")
2021-11-15 13:26:52 [warning  ] bar    process_name=MainProcess thread_name=MainThread

>>> structlog.get_logger("structlog").warning("foo", x=42)
2021-11-15 13:26:52 [warning  ] foo    process_name=MainProcess thread_name=MainThread x=42

>>> pathlib.Path("test.log").read_text()
2021-11-15 13:26:52 [warning  ] bar
2021-11-15 13:26:52 [warning  ] foo    x=42
```

(Sadly, you have to imagine the colors in the first two outputs.)

If you leave `foreign_pre_chain` as `None`, formatting will be left to `logging`.
Meaning: you can define a `format` for {class}`~structlog.stdlib.ProcessorFormatter` too!


[*python-json-logger*]: https://github.com/madzak/python-json-logger>
