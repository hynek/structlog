# Testing

*structlog* comes with tools for testing the logging behavior of your application.

If you need functionality similar to {meth}`unittest.TestCase.assertLogs`, or you want to capture all logs for some other reason, you can use the {func}`structlog.testing.capture_logs` context manager:

```{eval-rst}
.. doctest::

   >>> from structlog import get_logger
   >>> from structlog.testing import capture_logs
   >>> with capture_logs() as cap_logs:
   ...    get_logger().bind(x="y").info("hello")
   >>> cap_logs
   [{'x': 'y', 'event': 'hello', 'log_level': 'info'}]
```

Note that inside the context manager all configured processors are disabled.

:::{note}
`capture_logs()` relies on changing the configuration.
If you have *cache_logger_on_first_use* enabled for {doc}`performance <performance>`, any cached loggers will not be affected, so it’s recommended you do not enable it during tests.
:::

You can build your own helpers using {class}`structlog.testing.LogCapture`.
For example a [*pytest*](https://docs.pytest.org/) fixture to capture log output could look like this:

```
@pytest.fixture(name="log_output")
def fixture_log_output():
    return LogCapture()

@pytest.fixture(autouse=True)
def fixture_configure_structlog(log_output):
    structlog.configure(
        processors=[log_output]
    )

def test_my_stuff(log_output):
    do_something()
    assert log_output.entries == [...]
```

---

You can also use {class}`structlog.testing.CapturingLogger` (directly, or via {class}`~structlog.testing.CapturingLoggerFactory` that always returns the same logger) that is more low-level and great for unit tests:

```{eval-rst}
.. doctest::

   >>> import structlog
   >>> cf = structlog.testing.CapturingLoggerFactory()
   >>> structlog.configure(logger_factory=cf, processors=[structlog.processors.JSONRenderer()])
   >>> log = get_logger()
   >>> log.info("test!")
   >>> cf.logger.calls
   [CapturedCall(method_name='info', args=('{"event": "test!"}',), kwargs={})]
```

```{eval-rst}
.. testcleanup:: *

   import structlog
   structlog.reset_defaults()
```

---

Additionally *structlog* also ships with a logger that just returns whatever it gets passed into it: {class}`structlog.testing.ReturnLogger`.

```{eval-rst}
.. doctest::

   >>> from structlog import ReturnLogger
   >>> ReturnLogger().info(42) == 42
   True
   >>> obj = ["hi"]
   >>> ReturnLogger().info(obj) is obj
   True
   >>> ReturnLogger().info("hello", when="again")
   (('hello',), {'when': 'again'})
```
