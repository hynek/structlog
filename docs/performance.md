# Performance

Here are a few hints how to get the best performance out of *structlog* in production:

1. Use *structlog*'s native *BoundLogger* (created using {func}`structlog.make_filtering_bound_logger`) if you want to use level-based filtering.
   `return None` is hard to beat.

2. Avoid (frequently) calling log methods on loggers you get back from {func}`structlog.get_logger` or {func}`structlog.wrap_logger`.
   Since those functions are usually called in module scope and thus before you are able to configure them, they return a proxy object that assembles the correct logger on demand.

   Create a local logger if you expect to log frequently without binding:

   ```python
   logger = structlog.get_logger()
   def f():
      log = logger.bind()
      for i in range(1000000000):
         log.info("iterated", i=i)
   ```

   Since global scope lookups are expensive in Python, it's generally a good idea to copy frequently-used symbols into local scope.

3. Set the *cache_logger_on_first_use* option to `True` so the aforementioned on-demand loggers will be assembled only once and cached for future uses:

   ```python
   configure(cache_logger_on_first_use=True)
   ```

   This has two drawbacks:

   1. Later calls of {func}`~structlog.configure` don't have any effect on already cached loggers -- that shouldn't matter outside of {doc}`testing <testing>` though.
   2. The resulting bound logger is not pickleable.
      Therefore, you can't set this option if you e.g. plan on passing loggers around using `multiprocessing`.

4. Avoid sending your log entries through the standard library if you can: its dynamic nature and flexibility make it a major bottleneck.
   Instead use {class}`structlog.WriteLoggerFactory` or -- if your serializer returns bytes (e.g. [*orjson*]) -- {class}`structlog.BytesLoggerFactory`.

   You can still configure `logging` for packages that you don't control, but avoid it for your *own* log entries.

5. Use a faster JSON serializer than the standard library.
   Possible alternatives are among others are [*orjson*] or [*RapidJSON*].

## Example

Here's an example for a production-ready non-*asyncio* *structlog* configuration that's as fast as it gets:

```python
import logging
import structlog

structlog.configure(
    cache_logger_on_first_use=True,
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer(serializer=orjson.dumps),
    ],
    logger_factory=structlog.BytesLoggerFactory(),
)
```

It has the following properties:

- Caches all loggers on first use.
- Filters all log entries below the `info` log level **very** efficiently.
  The `debug` method literally consists of `return None`.
- Supports {doc}`contextvars` (thread-local contexts).
- Adds the log level name.
- Renders exceptions.
- Adds an [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) timestamp under the `timestamp` key in the UTC timezone.
- Renders the log entries as JSON using [*orjson*] which is faster than plain logging in `logging`.
- Uses {class}`structlog.BytesLoggerFactory` because *orjson* returns bytes.
  That saves encoding ping-pong.

Therefore a log entry might look like this:

```json
{"event":"hello","timestamp":"2020-11-17T09:54:11.900066Z"}
```

---

If you need standard library support for external projects, you can either just use a JSON formatter like [*python-json-logger*](https://pypi.org/project/python-json-logger/), or pipe them through *structlog* as documented in {doc}`standard-library`.

[*orjson*]: https://github.com/ijl/orjson
[*rapidjson*]: https://pypi.org/project/python-rapidjson/
[*simplejson*]: https://simplejson.readthedocs.io/
