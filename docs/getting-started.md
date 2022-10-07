# Getting Started

(install)=

## Installation

`structlog` can be easily installed using:

```
$ pip install structlog
```

If you want pretty exceptions in development (you know you do!), additionally install either [*rich*] or [*better-exceptions*].
Try both to find out which one you like better -- the screenshot in the README and docs homepage is rendered by *rich*.

On Windows, you also have to install [*colorama*] if you want colorful output beside exceptions.


## Your First Log Entry

A lot of effort went into making `structlog` accessible without reading pages of documentation.
And indeed, the simplest possible usage looks like this
(if you're reading this on a small screen, you may have to scroll the example horizontally to see the full output):

```{eval-rst}
.. doctest::

   >>> import structlog
   >>> log = structlog.get_logger()
   >>> log.info("hello, %s!", "world", key="value!", more_than_strings=[1, 2, 3])  # doctest: +SKIP
   2022-10-07 10:41.29 [info     ] hello, world!   key=value! more_strings=[1, 2, 3]
```

Here, `structlog` takes full advantage of its hopefully useful default settings:

- Output is sent to [standard out] instead of exploding into the user's face or doing nothing.
- It imitates standard library `logging`'s log levels for familiarity -- even if you're not using any of your integrations.
  By default, no level-based filtering is done, but it comes with a very fast filtering machinery in the form of `structlog.make_filtering_bound_logger()`.
- Like `logging`, positional arguments are [interpolated into the message string using %](https://docs.python.org/3/library/stdtypes.html#old-string-formatting).
  That might look dated, but it's *much* faster than using {any}`str.format` and allows ``structlog`` to be used as drop-in replacement for {mod}`logging` in more cases.
  If you *know* that the log entry is *always* gonna be logged out, just use [f-strings](https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals) which are the fastest.
- All keywords are formatted using `structlog.dev.ConsoleRenderer`.
  That in turn uses `repr` to serialize all values to strings.
  Thus, it's easy to add support for logging of your own objects[^prod-json].
- On Windows, if you have [*colorama*] installed, it's rendered in nice {doc}`colors <development>`.
  Other OSes do not need colorama for nice colors.
- If you have [*rich*] or [*better-exceptions*] installed, exceptions will be rendered in colors and with additional helpful information.

[^prod-json]: In production, you're more likely to use {class}`~structlog.processors.JSONRenderer` that can also be customized using a `__structlog__` method so you don't have to change your repr methods to something they weren't originally intended for.

It should be noted that even in most complex logging setups the example would still look just like that thanks to `configuration`.
Using the defaults, as above, is equivalent to:

```
import logging
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False
)
log = structlog.get_logger()
```

:::{note}
- `structlog.stdlib.recreate_defaults()` allows you to switch `structlog` to using standard library's `logging` module for output for better interoperability with just one function call.
- `structlog.make_filtering_bound_logger()` (re-)uses `logging`'s log levels, but doesn't use `logging` at all.
  The exposed API is `FilteringBoundLogger`.
- For brevity and to enable doctests, all further examples in `structlog`'s documentation use the more simplistic `structlog.processors.KeyValueRenderer()` without timestamps.
:::

There you go, structured logging!
However, this alone wouldn't warrant its own package.
After all, there's even a [recipe] on structured logging for the standard library.
So let's go a step further.

(building-ctx)=

## Building a Context

Imagine a hypothetical web application that wants to log out all relevant data with just the API from above:

```{literalinclude} code_examples/getting-started/imaginary_web.py
:language: python
```

The calls themselves are nice and straight to the point, however you're repeating yourself all over the place.
At this point, you'll be tempted to write a closure like:

```
def log_closure(event):
   log.info(event, user_agent=user_agent, peer_ip=peer_ip)
```

inside of the view.
Problem solved?
Not quite.
What if the parameters are introduced step by step?
Do you really want to have a logging closure in each of your views?

Let's have a look at a better approach:

```{literalinclude} code_examples/getting-started/imaginary_web_better.py
:language: python
```

Suddenly your logger becomes your closure!

For `structlog`, a log entry is just a dictionary called *event dict\[ionary\]*:

- You can pre-build a part of the dictionary step by step.
  These pre-saved values are called the *context*.
- As soon as an *event* happens -- which is a dictionary too -- it is merged together with the *context* to an *event dict* and logged out.
- If you don't like the concept of pre-building a context: just don't!
  Convenient key-value-based logging is great to have on its own.
- Python keeps dictionaries ordered by keys by default.
- The recommended way of binding values is the one in these examples: creating new loggers with a new context.
  If you're okay with giving up immutable local state for convenience, you can also use {doc}`context variables <contextvars>` for the context.


## Manipulating Log Entries in Flight

Now that your log events are dictionaries, it's also much easier to manipulate them than if it were plain strings.

To facilitate that, `structlog` has the concept of {doc}`processor chains <processors>`.
A processor is a callable like a function that receives the event dictionary along with two other arguments and returns a new event dictionary that may or may not differ from the one it got passed.
The next processor in the chain receives that returned dictionary instead of the original one.

Let's assume you wanted to add a timestamp to every event dict.
The processor would look like this:

```{eval-rst}
.. doctest::

  >>> import datetime
  >>> def timestamper(_, __, event_dict):
  ...     event_dict["time"] = datetime.datetime.now().isoformat()
  ...     return event_dict
```

Plain Python, plain dictionaries.
Now you have to tell `structlog` about your processor by {doc}`configuring <configuration>` it:

```{eval-rst}
.. doctest::

  >>> structlog.configure(processors=[timestamper, structlog.processors.KeyValueRenderer()])
  >>> structlog.get_logger().info("hi")  # doctest: +SKIP
  event='hi' time='2018-01-21T09:37:36.976816'

```

## Rendering

Finally you want to have control over the actual format of your log entries.

As you may have noticed in the previous section, renderers are just processors too.
It's also important to note, that they do not necessarily have to render your event dictionary to a string.
The output that is required from the renderer depends on the input that the *logger* that is wrapped by `structlog` needs.

However, in most cases it's gonna be strings.

So assuming you want to follow {doc}`best practices <logging-best-practices>` and render your event dictionary to JSON that is picked up by a log aggregation system like ELK or Graylog, `structlog` comes with batteries included -- you just have to tell it to use its {class}`~structlog.processors.JSONRenderer`:

```{eval-rst}
.. doctest::

  >>> structlog.configure(processors=[structlog.processors.JSONRenderer()])
  >>> structlog.get_logger().info("hi")
  {"event": "hi"}

```

## `structlog` and Standard Library's `logging`

`structlog`'s primary application isn't printing though.
Instead, it's intended to wrap your *existing* loggers and **add** *structure* and *incremental context building* to them.
For that, `structlog` is *completely* agnostic of your underlying logger -- you can use it with any logger you like.

The most prominent example of such an 'existing logger' is without doubt the logging module in the standard library.
To make this common case as simple as possible, `structlog` comes with some tools to help you:

```{eval-rst}
.. doctest::

   >>> import logging
   >>> logging.basicConfig()
   >>> from structlog.stdlib import LoggerFactory
   >>> structlog.configure(logger_factory=LoggerFactory())  # doctest: +SKIP
   >>> log = structlog.get_logger()
   >>> log.warning("it works!", difficulty="easy")  # doctest: +SKIP
   WARNING:structlog...:difficulty='easy' event='it works!'
```

In other words, you tell `structlog` that you would like to use the standard library logger factory and keep calling {func}`~structlog.get_logger` like before.

Since `structlog` is mainly used together with standard library's logging, there's {doc}`more <standard-library>` goodness to make it as fast and convenient as possible.

## Liked what you saw?

Now you're all set for the rest of the user's guide and can start reading about {doc}`bound loggers <loggers>` -- the heart of `structlog`.
If you want to see more code, make sure to check out the `examples`!


[*better-exceptions*]: https://github.com/qix-/better-exceptions
[*colorama*]: https://pypi.org/project/colorama/
[recipe]: https://docs.python.org/3/howto/logging-cookbook.html#implementing-structured-logging
[*rich*]: https://github.com/Textualize/rich
[standard out]: https://en.wikipedia.org/wiki/Standard_out#Standard_output_.28stdout.29
