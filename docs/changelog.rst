Changelog
=========
- :bug:`20` :class:`structlog.ReturnLogger` now has an exception function.
- :bug:`-` Various doc fixes.
- :release:`0.4.0 <2013-11-10>`
- :feature:`6` Add :class:`structlog.processors.StackInfoRenderer` for adding stack information to log entries without involving exceptions.
  Also added it to default processor chain.
- :feature:`12` Allow optional positional arguments for :func:`structlog.get_logger` that are passed to logger factories.
  The standard library factory uses this for explicit logger naming.
- :feature:`-` Add :class:`structlog.processors.ExceptionPrettyPrinter` for development and testing when multiline log entries aren't just acceptable but even helpful.
- :feature:`-` Allow the standard library name guesser to ignore certain frame names.
  This is useful together with frameworks.
- :feature:`5` Add meta data (e.g. function names, line numbers) extraction for wrapped stdlib loggers.
- :release:`0.3.2 <2013-09-27>`
- :bug:`-` Fix stdlib's name guessing.
- :release:`0.3.1 <2013-09-26>`
- :bug:`-` Add forgotten :class:`structlog.processors.TimeStamper` to API documentation.
- :release:`0.3.0 <2013-09-23>`
- :support:`-` Greatly enhanced and polished the documentation and added a new theme based on Write The Docs, requests, and Flask.
  See :doc:`license`.
- :feature:`-` Add Python Standard Library-specific BoundLogger that has an explicit API instead of intercepting unknown method calls.
  See :class:`structlog.stdlib.BoundLogger`.
- :feature:`-` :class:`structlog.ReturnLogger` now allows arbitrary positional and keyword arguments.
- :feature:`-` Add Twisted-specific BoundLogger that has an explicit API instead of intercepting unknown method calls.
  See :class:`structlog.twisted.BoundLogger`.
- :feature:`-` Allow logger proxies that are returned by :func:`structlog.get_logger` and :func:`structlog.wrap_logger` to cache the BoundLogger they assemble according to configuration on first use.
  See :doc:`performance` and the `cache_logger_on_first_use` of :func:`structlog.configure` and :func:`structlog.wrap_logger`.
- :feature:`-` Extract a common base class for loggers that does nothing except keeping the context state.
  This makes writing custom loggers much easier and more straight-forward.
  See :class:`structlog.BoundLoggerBase`.
- :release:`0.2.0 <2013-09-17>`
- :feature:`-` Promote to stable, thus henceforth a strict backward compatibility policy is put into effect.
  See :ref:`contributing`.
- :feature:`-` Add `key_order` option to :class:`structlog.processors.KeyValueRenderer` for more predictable log entries with any `dict` class.
- :feature:`-` :class:`structlog.PrintLogger` now uses proper I/O routines and is thus viable not only for examples but also for production.
- :feature:`-` :doc:`Enhance Twisted support <twisted>` by offering JSONification of non-structlog log entries.
- :feature:`-` Allow for custom serialization in :class:`structlog.twisted.JSONRenderer` without abusing ``__repr__``.
- :release:`0.1.0 <2013-09-16>`
- :feature:`-` Initial work.
