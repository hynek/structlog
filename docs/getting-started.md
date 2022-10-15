# Getting Started

(install)=

## Installation

You can install *structlog* from [PyPI](https://pypi.org/project/structlog/) using *pip*:

```console
$ python -m pip install structlog
```

If you want pretty exceptions in development (you know you do!), additionally install either [*Rich*] or [*better-exceptions*].
Try both to find out which one you like better -- the screenshot in the README and docs homepage is rendered by *Rich*.

On **Windows**, you also have to install [*Colorama*](https://pypi.org/project/colorama/) if you want colorful output beside exceptions.


## Your First Log Entry

A lot of effort went into making *structlog* accessible without reading pages of documentation.
As a result, the simplest possible usage looks like this:

```{eval-rst}
.. doctest::

   >>> import structlog
   >>> log = structlog.get_logger()
   >>> log.info("hello, %s!", "world", key="value!", more_than_strings=[1, 2, 3])  # doctest: +SKIP
   2022-10-07 10:41:29 [info     ] hello, world!   key=value! more_than_strings=[1, 2, 3]
```

Here, *structlog* takes advantage of its default settings:

- Output is sent to **[standard out](https://en.wikipedia.org/wiki/Standard_out#Standard_output_.28stdout.29)** instead doing nothing.
- It **imitates** standard library {mod}`logging`'s **log level names** for familiarity.
  By default, no level-based filtering is done, but it comes with a **very fast [filtering machinery](filtering)**.
- Like in `logging`, positional arguments are [**interpolated into the message string using %**](https://docs.python.org/3/library/stdtypes.html#old-string-formatting).
  That might look dated, but it's *much* faster than using {any}`str.format` and allows *structlog* to be used as drop-in replacement for {mod}`logging`.
  If you *know* that the log entry is *always* gonna be logged out, just use [f-strings](https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals) which are the fastest.
- All keywords are formatted using {class}`structlog.dev.ConsoleRenderer`.
  That in turn uses {func}`repr` to serialize **any value to a string**.
- It's rendered in nice **{doc}`colors <console-output>`**.
- If you have [*Rich*] or [*better-exceptions*] installed, **exceptions** will be rendered in **colors** and with additional **helpful information**.

Please note that even in most complex logging setups the example would still look just like that thanks to {doc}`configuration`.
Using the defaults, as above, is equivalent to:

```python
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
- {func}`structlog.stdlib.recreate_defaults()` allows you to switch *structlog* to using standard library's `logging` module for output for better interoperability with just one function call.
- {func}`~structlog.make_filtering_bound_logger()` (re-)uses {any}`logging`'s log levels, but doesn't use `logging` at all.
  The exposed API is {class}`~structlog.typing.FilteringBoundLogger`.
- For brevity and to enable doctests, all further examples in *structlog*'s documentation use the more simplistic {class}`~structlog.processors.KeyValueRenderer()` without timestamps.
:::

Here you go, structured logging!


However, this alone wouldn't warrant its own package.
After all, there's even a [recipe] on structured logging for the standard library.
So let's go a step further.

(building-ctx)=

## Building a Context

Imagine a hypothetical web application that wants to log out all relevant data with just the APIs that we've introduced so far:

```python
def view(request):
    user_agent = request.get("HTTP_USER_AGENT", "UNKNOWN")
    peer_ip = request.client_addr
    if something:
        log.info("something", user_agent=user_agent, peer_ip=peer_ip)
        return "something"
    elif something_else:
        log.info("something_else", user_agent=user_agent, peer_ip=peer_ip)
        return "something_else"
    else:
        log.info("else", user_agent=user_agent, peer_ip=peer_ip)
        return "else"
```

The calls themselves are nice and straight to the point, however you're repeating yourself all over the place.
It's easy to forget to add a key-value pair in one of the incantations.

At this point, you'll be tempted to write a closure like:

```python
def log_closure(event):
   log.info(event, user_agent=user_agent, peer_ip=peer_ip)
```

inside of the view.
Problem solved?
Not quite.
What if the parameters are introduced step by step?
And do you really want to have a logging closure in each of your views?

Let's have a look at a better approach:

```python
def view(request):
    log = logger.bind(
        user_agent=request.get("HTTP_USER_AGENT", "UNKNOWN"),
        peer_ip=request.client_addr,
    )

    if foo := request.get("foo"):
        log = log.bind(foo=foo)

    if something:
        log.info("something")
        return "something"
    elif something_else:
        log.info("something_else")
        return "something_else"
    else:
        log.info("else")
        return "else"

```

Suddenly your logger becomes your closure!

---

To *structlog*, a log entry is just a dictionary called *event dict\[ionary\]*:

- You can pre-build a part of the dictionary step by step.
  These pre-saved values are called the *context*.
- As soon as an *event* happens -- which are the `kwargs` of the log call -- it is merged together with the *context* to an *event dict* and logged out.
- Each logger with its context is *immutable*.
  You manipulate the context by creating new loggers using `bind()` and `unbind()`.

The last point is very clean and easy to reason about, but sometimes it's useful to store _some_ data globally.

In our example above the peer IP comes to mind.
There's no point in extracting it in every view!
For that, *structlog* gives you thread-local context storage based on the {mod}`contextvars` module:

```pycon
>>> structlog.contextvars.bind_contextvars(peer_ip="1.2.3.4")
>>> structlog.get_logger().info("something")
2022-10-10 10:18:05 [info     ] something    peer_ip=1.2.3.4
```

See {doc}`contextvars` for more information and a more complete example.


## Manipulating Log Entries in Flight

Now that your log events are dictionaries, it's also much easier to manipulate them than if they were plain strings.

To facilitate that, *structlog* has the concept of {doc}`processor chains <processors>`.
A processor is a function that receives the event dictionary along with two other arguments and returns a new event dictionary that may or may not differ from the one it got passed.
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
Now you have to tell *structlog* about your processor by {doc}`configuring <configuration>` it:

```{eval-rst}
.. doctest::

  >>> structlog.configure(processors=[timestamper, structlog.processors.KeyValueRenderer()])
  >>> structlog.get_logger().info("hi")  # doctest: +SKIP
  event='hi' time='2018-01-21T09:37:36.976816'
```


## Rendering

Finally you want to have control over the actual format of your log entries.

As you may have noticed in the previous section, renderers are just processors too.
The type of the return value that is required from the renderer depends on the input that the *logger* that is wrapped by *structlog* needs.
While usually it's a string or bytes, there's no rule saying it _has_ to be a string!

So assuming you want to follow [best practices](logging-best-practices.md) and render your event dictionary to JSON that is picked up by a log aggregation system like ELK or Graylog, *structlog* comes with batteries included -- you just have to tell it to use its {class}`~structlog.processors.JSONRenderer`:

```{eval-rst}
.. doctest::

  >>> structlog.configure(processors=[structlog.processors.JSONRenderer()])
  >>> structlog.get_logger().info("hi")
  {"event": "hi"}
```


## *structlog* and Standard Library's `logging`

While *structlog*'s loggers are very fast and sufficient for the majority of our users, you're not bound to them.
Instead, it's been designed from day one to wrap your *existing* loggers and **add** *structure* and *incremental context building* to them.

The most prominent example of such an "existing logger" is certainly the logging module in the standard library.
To make this common case as simple as possible, *structlog* comes with [some tools](standard-library.md) to help you.

As noted before, the fastest way to transform *structlog* into a `logging`-friendly package is calling {func}`structlog.stdlib.recreate_defaults()`.


## Liked what you saw?

Now you're all set for the rest of the user's guide and can start reading about [bound loggers](bound-loggers.md) -- the heart of *structlog*.


[*better-exceptions*]: https://github.com/qix-/better-exceptions
[recipe]: https://docs.python.org/3/howto/logging-cookbook.html#implementing-structured-logging
[*Rich*]: https://github.com/Textualize/rich
