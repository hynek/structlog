# Why …

## … Structured Logging?

> I believe the widespread use of format strings in logging is based on two presumptions:
>
> - The first level consumer of a log message is a human.
> - The programmer knows what information is needed to debug an issue.
>
> I believe these presumptions are **no longer correct** in server side software.
>
> —<cite>[Paul Querna](https://paul.querna.org/articles/2011/12/26/log-for-machines-in-json/)</cite>

Structured logging means that you don't write hard-to-parse and hard-to-keep-consistent prose in your log entries.
Instead, you log *events* that happen in a *context* of key-value pairs.


## … structlog?

## Easier Logging

You can stop writing prose and start thinking in terms of an event that happens in the context of key-value pairs:

```pycon
>>> from structlog import get_logger
>>> log = get_logger()
>>> log.info("key_value_logging", out_of_the_box=True, effort=0)
2020-11-18 09:17:09 [info     ] key_value_logging    effort=0 out_of_the_box=True
```

Each log entry is a meaningful dictionary instead of an opaque string now!

That said, `structlog` is not taking anything away from you.
You can still use string interpolation using positional arguments:

```pycon
>>> log.info("Hello, %s!", "world")
2022-10-10 07:19:25 [info     ] Hello, world!
```

## Data Binding

Since log entries are dictionaries, you can start binding and re-binding key-value pairs to your loggers to ensure they are present in every following logging call:

```pycon
>>> log = log.bind(user="anonymous", some_key=23)
>>> log = log.bind(user="hynek", another_key=42)
>>> log.info("user.logged_in", happy=True)
2020-11-18 09:18:28 [info     ] user.logged_in    another_key=42 happy=True some_key=23 user=hynek
```

You can also bind key-value pairs to {doc}`context variables <contextvars>` that look global, but are local to your thread or *asyncio* context (i.e. usually your request).


## Powerful Pipelines

Each log entry goes through a [processor pipeline](processors.md) that is just a chain of functions that receive a dictionary and return a new dictionary that gets fed into the next function.
That allows for simple but powerful data manipulation:

```python
def timestamper(logger, log_method, event_dict):
    """Add a timestamp to each log entry."""
    event_dict["timestamp"] = time.time()
    return event_dict
```

There are [plenty of processors](structlog.processors) for most common tasks coming with `structlog`:

- Collectors of [call stack information](structlog.processors.StackInfoRenderer) ("How did this log entry happen?"),
- …and [exceptions](structlog.processors.format_exc_info) ("What happened‽").
- Flexible [timestamping](structlog.processors.TimeStamper).


## Formatting

`structlog` is completely flexible about *how* the resulting log entry is emitted.
Since each log entry is a dictionary, it can be formatted to **any** format:

- A colorful key-value format for [local development](https://www.structlog.org/en/stable/development.html),
- [JSON](https://www.structlog.org/en/stable/api.html#structlog.processors.JSONRenderer) for easy parsing,
- or some standard format you have parsers for like *nginx* or Apache *httpd*.

Internally, formatters are processors whose return value (usually a string) is passed into loggers that are responsible for the output of your message.
`structlog` comes with multiple useful formatters out-of-the-box.


## Output

`structlog` is also flexible with the final output of your log entries:

- A **built-in** lightweight printer like in the examples above.
  Easy to use and fast.
- Use the [**standard library**](standard-library.md)'s or [**Twisted**](twisted.md)'s logging modules for compatibility.
  In this case `structlog` works like a wrapper that formats a string and passes them off into existing systems that won't know that `structlog` even exists.

  Or the other way round: `structlog` comes with a `logging` formatter that allows for processing third party log records.
- Don't format it to a string at all!
  `structlog` passes you a dictionary and you can do with it whatever you want.
  Reported use cases are sending them out via network or saving them in a database.

## Highly Testable

`structlog` is thoroughly tested and we see it as our duty to help you to achieve the same in *your* applications.
That's why it ships with a [test helpers](https://www.structlog.org/en/stable/testing.html) to introspect your application's logging behavior with little-to-no boilerplate.
