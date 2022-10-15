# Configuration

The focus of *structlog* has always been to be flexible to a fault.
The goal is that a user can use it with *any* logger of their own that is wrapped by *structlog*.

That's the reason why there's an overwhelming amount of knobs to tweak, but
– ideally – once you find your configuration, you don't touch it ever again and, more importantly:
don't see any of it in your application code.

---

Let's start at the end and introduce the ultimate convenience function that relies purely on configuration: {func}`structlog.get_logger`.

The goal is to reduce your per-file application logging boilerplate to:

```
import structlog

logger = structlog.get_logger()
```

To that end, you'll have to call {func}`structlog.configure` on app initialization.
You can call {func}`structlog.configure` repeatedly and only set one or more settings -- the rest will not be affected.

If necessary, you can always reset your global configuration back to default values using {func}`structlog.reset_defaults`.
That can be handy in tests.

At any time, you can check whether and how *structlog* is configured using {func}`structlog.is_configured` and {func}`structlog.get_config`}:

```pycon
>>> structlog.is_configured()
False
>>> structlog.configure(logger_factory=structlog.stdlib.LoggerFactory)
>>> structlog.is_configured()
True
>>> cfg = structlog.get_config()
>>> cfg["logger_factory"]
<class 'structlog.stdlib.LoggerFactory'>
```

:::{important}
Since you'll call {func}`structlog.get_logger` in module scope, it runs at import time *before* you had a chance to configure *structlog*.
Therefore it returns a **lazy proxy** that returns a correctly configured *bound logger* on its first call to one of the context-managing methods like `bind()`.

Thus, you must never call `new()` or `bind()` in module or class scope because , you will receive a logger configured with *structlog*'s default values.
Use {func}`~structlog.get_logger`'s `initial_values` to achieve pre-populated contexts.

To enable you to log with the module-global logger, it will create a temporary *bound logger* **on each call**.
Therefore if you have nothing to bind but intend to do lots of log calls in a function, it makes sense performance-wise to create a local logger by calling `bind()` or `new()` without any parameters.
See also {doc}`performance`.
:::


## What To Configure

You can find the details in the API documentation of {func}`structlog.configure`, but let's introduce the most important ones at a high level first.


### Wrapper Classes

You've met {doc}`bound-loggers` in the last chapter.
They're the objects returned by {func}`~structlog.get_logger` and allow to bind key-value pairs into their private context.
You can configure their type using the `wrapper_class` keyword.

Whenever you bind or unbind data to a *bound logger*, this class is instantiated with the new context and returned.


### Logger Factories

We've already talked about wrapped loggers responsible for the output, but until now we haven't explained where they come from until now.
Unlike with *bound loggers*, you often need more flexibility when instantiating them.
Therefore you don't configure a class; you configure a *factory* using the `logger_factory` keyword.

It's a callable that returns the logger that gets wrapped and returned.
In the simplest case, it's a function that returns a logger -- or just a class.
But you can also pass in an instance of a class with a `__call__` method for more complicated setups.

These will be passed to the logger factories.
For example, if you use `structlog.get_logger("a name")` and configure *structlog* to use the standard library {class}`~structlog.stdlib.LoggerFactory`, which has support for positional parameters, the returned logger will have the name `"a name"`.

For the common cases of standard library logging and Twisted logging, *structlog* comes with two factories built right in:

- {class}`structlog.stdlib.LoggerFactory`
- {class}`structlog.twisted.LoggerFactory`

So all it takes to use standard library {mod}`logging` for output is:

```
>>> from structlog import get_logger, configure
>>> from structlog.stdlib import LoggerFactory
>>> configure(logger_factory=LoggerFactory())
>>> log = get_logger()
>>> log.critical("this is too easy!")
event='this is too easy!'
```

By using *structlog*'s {class}`structlog.stdlib.LoggerFactory`, it is also ensured that variables like function names and line numbers are expanded correctly in your log format.
See {doc}`standard-library` for more details.

Calling {func}`structlog.get_logger` without configuration gives you a perfectly useful {class}`structlog.PrintLogger`.
We don't believe silent loggers are a sensible default.


### Processors

You will meet {doc}`processors` in the next chapter.
They are configured using the `processors` keyword that takes an {class}`~collections.abc.Iterable` of callables that act as processors.
