# Custom Wrappers

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

The object that is returned by {func}`structlog.get_logger()` is called a *bound logger*, or a *wrapper class* (because it wraps the original logger that takes care of the output).
This wrapper class is [configurable](configuration.md).

Originally, `structlog` used a generic *bound logger* called {class}`structlog.BoundLogger` by default.
It can wrap *any* logger class by intercepting unknown method names and proxying them to the wrapped logger (that is in charge of output).

Nowadays, the default is a {class}`structlog.types.FilteringBoundLogger` that imitates standard library's log levels with the possibility of efficiently filtering at a certain level (inactive log methods are a plain `return None`).

If you're integrating with {mod}`logging` or Twisted, you may was to use one of their specific *bound loggers* ({class}`structlog.stdlib.BoundLogger` and {class}`structlog.twisted.BoundLogger`, respectively).

---

But you can also write your own wrapper class.
To make it easy for you, `structlog` comes with the class {class}`structlog.BoundLoggerBase` which takes care of all data binding duties so you just add your log methods if you choose to sub-class it.

(wrapper-class-example)=

## Example

It's easiest to demonstrate with an example:

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
