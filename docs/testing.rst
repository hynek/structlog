Testing
-------

``structlog`` comes with tools for testing the logging behavior of your application.

If you need functionality similar to `unittest.TestCase.assertLogs`, or you want to capture all logs for some other reason, you can use the `structlog.testing.capture_logs` context manager:

.. doctest::

   >>> from structlog import get_logger
   >>> from structlog.testing import capture_logs
   >>> with capture_logs() as cap_logs:
   ...    get_logger().bind(x="y").info("hello")
   >>> cap_logs
   [{'x': 'y', 'event': 'hello', 'log_level': 'info'}]

You can build your own helpers using `structlog.testing.LogCapture`.
For example a `pytest <https://docs.pytest.org/>`_ fixture to capture log output could look like this::

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

----

Additionally ``structlog`` also ships with a logger that just returns whatever it gets passed into it: `structlog.testing.ReturnLogger`.

.. doctest::

   >>> from structlog import ReturnLogger
   >>> ReturnLogger().msg(42) == 42
   True
   >>> obj = ["hi"]
   >>> ReturnLogger().msg(obj) is obj
   True
   >>> ReturnLogger().msg("hello", when="again")
   (('hello',), {'when': 'again'})
