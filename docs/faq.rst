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
