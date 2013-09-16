Changelog
=========

- :feature:`0` Add `key_order` option to :class:`structlog.processors.KeyValueRenderer` for more predictable log entries with any `dict` class.
- :feature:`0` :class:`structlog.PrintLogger` now uses proper I/O routines and is thus viable not only for examples but also for production.
- :feature:`0` :ref:`Enhance Twisted support <twisted>` by offering JSONification of non-structlog log entries.
- :feature:`0` Allow custom serialization in :class:`structlog.twisted.JSONRenderer` without abusing ``__repr__``.
- :release:`0.1.0 <2013-09-16>`
- :feature:`0` Initial work.
