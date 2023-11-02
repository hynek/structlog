# Performance

Here are a few hints how to get the best performance out of *structlog* in production:

- Use *structlog*'s native *BoundLogger* (created using {func}`structlog.make_filtering_bound_logger`) if you want to use level-based filtering.
  `return None` is hard to beat.

- Avoid (frequently) calling log methods on loggers you get back from {func}`structlog.get_logger` or {func}`structlog.wrap_logger`.
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

- Set the *cache_logger_on_first_use* option to `True` so the aforementioned on-demand loggers will be assembled only once and cached for future uses:

  ```python
  configure(cache_logger_on_first_use=True)
  ```

  This has two drawbacks:

  1. Later calls of {func}`~structlog.configure` don't have any effect on already cached loggers -- that shouldn't matter outside of {doc}`testing <testing>` though.
  2. The resulting bound logger is not pickleable.
      Therefore, you can't set this option if you, for example, plan on passing loggers around using {mod}`multiprocessing`.

- Avoid sending your log entries through the standard library if you can: its dynamic nature and flexibility make it a major bottleneck.
  Instead use {class}`structlog.WriteLoggerFactory` or -- if your serializer returns bytes (for example, [*orjson*] or [*msgspec*]) -- {class}`structlog.BytesLoggerFactory`.

  You can still configure `logging` for packages that you don't control, but avoid it for your *own* log entries.

- Configure {class}`~structlog.processors.JSONRenderer` to use a faster JSON serializer than the standard library.
  Possible alternatives are among others are [*orjson*], [*msgspec*], or [RapidJSON](https://pypi.org/project/python-rapidjson/).

- Be conscious about whether and how you use *structlog*'s *asyncio* support.
  While it's true that moving log processing into separate threads prevents your application from hanging, it also comes with a performance cost.

  Decide judiciously whether or not you're willing to pay that price.
  If your processor chain has a good and predictable performance without external dependencies (as it should), it might not be worth it.


## Example

Here's an example for a production-ready *structlog* configuration that's as fast as it gets:

```python
import logging
import orjson
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
- Supports {doc}`contextvars` (thread-local contexts outside of *asyncio*).
- Adds the log level name.
- Renders exceptions into the `exception` key.
- Adds an [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) timestamp under the `timestamp` key in the UTC timezone.
- Renders the log entries as JSON using [*orjson*] which is faster than *plain* logging in {mod}`logging`.
- Uses {class}`structlog.BytesLoggerFactory` because *orjson* returns bytes.
  That saves encoding ping-pong.

Therefore a log entry might look like this:

```json
{"event":"hello","level":"info","timestamp":"2023-11-02T08:03:38.298565Z"}
```

---

If you need standard library support for external projects, you can either just use a JSON formatter like [*python-json-logger*](https://pypi.org/project/python-json-logger/), or pipe them through *structlog* as documented in {doc}`standard-library`.

[*orjson*]: https://github.com/ijl/orjson
[*msgspec*]: https://jcristharif.com/msgspec/
