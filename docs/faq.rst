Frequently Asked Questions
==========================

I try to bind key-value pairs but they don't appear in the log files?
  ``structlog``\ 's loggers are *immutable*.
  Meaning that you have to use the logger that is returned from ``bind()``:

  .. doctest::

    >>> import structlog
    >>> log = structlog.get_logger()
    >>> log.bind(x=42)  # doctest: +SKIP
    >>> log.msg("hello")
    event='hello'
    >>> new_log = log.bind(x=42)
    >>> new_log.msg("hello")
    x=42 event='hello'


How can I make third party components log in JSON too?
   Since Twisted's logging is nicely composable, ``structlog`` comes with `integration support <http://www.structlog.org/en/stable/twisted.html#bending-foreign-logging-to-your-will>`_ out of the box.

   The standard library is a bit more complicated and tough to solve universally.
   But generally speaking, all you need is a handler that will redirect standard library logging into ``structlog``.
   For example like this::

      import logging

      class StructlogHandler(logging.Handler):
          """
          Feeds all events back into structlog.
          """
          def __init__(self, *args, **kw):
              super(StructlogHandler, self).__init__(*args, **kw)
              self._log = structlog.get_logger()

          def emit(self, record):
              self._log.log(record.levelno, record.msg, name=record.name)

      root_logger = logging.getLogger()
      root_logger.addHandler(StructlogHandler())

   There are two things to keep in mind:

     #. You can't log out using the standard library since that would create an infinite loop.
        In other words you have to use for example ``PrintLogger`` for actual output (which is nothing wrong with).
     #. You can't affect the logging of your parent process.
        So for example if you're running a web application as `Gunicorn <http://gunicorn.org>`_ workers, you have to configure Gunicorn's logging separately if you want it to write JSON logs.
        In these cases a library like `python-json-logger <https://github.com/madzak/python-json-logger>`_ should come in handy.
