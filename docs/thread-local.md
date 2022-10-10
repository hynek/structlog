# Legacy Thread-local Context

:::{attention}
The `structlog.threadlocal` module is deprecated as of `structlog` 22.1.0 in favor of {doc}`contextvars`.

The standard library {mod}`contextvars` module provides a more feature-rich superset of the thread-local APIs and works with thread-local data, async code, and greenlets.

Therefore, as of 22.1.0, the `structlog.threadlocal` module is frozen and will be removed after May 2023.
:::

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


## The `merge_threadlocal` Processor

`structlog` provides a simple set of functions that allow explicitly binding certain fields to a global (thread-local) context and merge them later using a processor into the event dict.

The general flow of using these functions is:

- Use {func}`structlog.configure` with {func}`structlog.threadlocal.merge_threadlocal` as your first processor.
- Call {func}`structlog.threadlocal.clear_threadlocal` at the beginning of your request handler (or whenever you want to reset the thread-local context).
- Call {func}`structlog.threadlocal.bind_threadlocal` as an alternative to your bound logger's `bind()` when you want to bind a particular variable to the thread-local context.
- Use `structlog` as normal.
  Loggers act as they always do, but the {func}`structlog.threadlocal.merge_threadlocal` processor ensures that any thread-local binds get included in all of your log messages.
- If you want to access the thread-local storage, you use {func}`structlog.threadlocal.get_threadlocal` and {func}`structlog.threadlocal.get_merged_threadlocal`.

These functions map 1:1 to the {doc}`contextvars` APIs, so please use those instead:

- {func}`structlog.contextvars.merge_contextvars`
- {func}`structlog.contextvars.clear_contextvars`
- {func}`structlog.contextvars.bind_contextvars`
- {func}`structlog.contextvars.get_contextvars`
- {func}`structlog.contextvars.get_merged_contextvars`


## Thread-local Contexts

`structlog` also provides thread-local context storage in a form that you may already know from [*Flask*](https://flask.palletsprojects.com/en/latest/design/#thread-locals) and that makes the *entire context* global to your thread or greenlet.

This makes its behavior more difficult to reason about which is why we generally recommend to use the {func}`~structlog.contextvars.merge_contextvars` route.
Therefore, there are currently no plans to re-implement this behavior on top of context variables.


### Wrapped Dicts

In order to make your context thread-local, `structlog` ships with a function that can wrap any dict-like class to make it usable for thread-local storage: {func}`structlog.threadlocal.wrap_dict`.

Within one thread, every instance of the returned class will have a *common* instance of the wrapped dict-like class:

```{eval-rst}
.. doctest::

   >>> from structlog.threadlocal import wrap_dict
   >>> WrappedDictClass = wrap_dict(dict)
   >>> d1 = WrappedDictClass({"a": 1})
   >>> d2 = WrappedDictClass({"b": 2})
   >>> d3 = WrappedDictClass()
   >>> d3["c"] = 3
   >>> d1 is d3
   False
   >>> d1 == d2 == d3 == WrappedDictClass()
   True
   >>> d3  # doctest: +ELLIPSIS
   <WrappedDict-...({'a': 1, 'b': 2, 'c': 3})>

```

To enable thread-local context use the generated class as the context class:

```python
configure(context_class=WrappedDictClass)
```

:::{note}
Creation of a new `BoundLogger` initializes the logger's context as `context_class(initial_values)`, and then adds any values passed via `.bind()`.
As all instances of a wrapped dict-like class share the same data, in the case above, the new logger's context will contain all previously bound values in addition to the new ones.
:::

`structlog.threadlocal.wrap_dict` returns always a completely *new* wrapped class:

```{eval-rst}
.. doctest::

   >>> from structlog.threadlocal import wrap_dict
   >>> WrappedDictClass = wrap_dict(dict)
   >>> AnotherWrappedDictClass = wrap_dict(dict)
   >>> WrappedDictClass() != AnotherWrappedDictClass()
   True
   >>> WrappedDictClass.__name__  # doctest: +SKIP
   WrappedDict-41e8382d-bee5-430e-ad7d-133c844695cc
   >>> AnotherWrappedDictClass.__name__   # doctest: +SKIP
   WrappedDict-e0fc330e-e5eb-42ee-bcec-ffd7bd09ad09

```

In order to be able to bind values temporarily to a logger, `structlog.threadlocal` comes with a [context manager](https://docs.python.org/2/library/stdtypes.html#context-manager-types): {func}`structlog.threadlocal.tmp_bind`:

```{eval-rst}
.. testsetup:: ctx

   from structlog import PrintLogger, wrap_logger
   from structlog.threadlocal import tmp_bind, wrap_dict
   WrappedDictClass = wrap_dict(dict)
   log = wrap_logger(PrintLogger(), context_class=WrappedDictClass)
```

```{eval-rst}
.. doctest:: ctx

   >>> log.bind(x=42)  # doctest: +ELLIPSIS
   <BoundLoggerFilteringAtNotset(context=<WrappedDict-...({'x': 42})>, ...)>
   >>> log.msg("event!")
   x=42 event='event!'
   >>> with tmp_bind(log, x=23, y="foo") as tmp_log:
   ...     tmp_log.msg("another event!")
   x=23 y='foo' event='another event!'
   >>> log.msg("one last event!")
   x=42 event='one last event!'
```

The state before the `with` statement is saved and restored once it's left.

If you want to detach a logger from thread-local data, there's {func}`structlog.threadlocal.as_immutable`.


#### Downsides & Caveats

The convenience of having a thread-local context comes at a price though:

:::{warning}
- If you can't rule out that your application re-uses threads, you *must* remember to **initialize your thread-local context** at the start of each request using {func}`~structlog.BoundLogger.new` (instead of {func}`~structlog.BoundLogger.bind`).
  Otherwise you may start a new request with the context still filled with data from the request before.

- **Don't** stop assigning the results of your `bind()`s and `new()`s!

  **Do**:

  ```
  log = log.new(y=23)
  log = log.bind(x=42)
  ```

  **Don't**:

  ```
  log.new(y=23)
  log.bind(x=42)
  ```

  Although the state is saved in a global data structure, you still need the global wrapped logger produce a real bound logger.
  Otherwise each log call will result in an instantiation of a temporary BoundLogger.

  See `configuration` for more details.

- It [doesn't play well](https://github.com/hynek/structlog/issues/296) with `os.fork` and thus `multiprocessing` (unless configured to use the `spawn` start method).
:::


## API

```{eval-rst}
.. module:: structlog.threadlocal
```

```{eval-rst}
.. autofunction:: bind_threadlocal
```

```{eval-rst}
.. autofunction:: unbind_threadlocal
```

```{eval-rst}
.. autofunction:: bound_threadlocal
```

```{eval-rst}
.. autofunction:: get_threadlocal
```

```{eval-rst}
.. autofunction:: get_merged_threadlocal
```

```{eval-rst}
.. autofunction:: merge_threadlocal
```

```{eval-rst}
.. autofunction:: clear_threadlocal
```

```{eval-rst}
.. autofunction:: wrap_dict
```

```{eval-rst}
.. autofunction:: tmp_bind(logger, **tmp_values)
```

```{eval-rst}
.. autofunction:: as_immutable
```
