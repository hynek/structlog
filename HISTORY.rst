.. :changelog:

History
-------

0.2.0 (unreleased)
^^^^^^^^^^^^^^^^^^

- Allow custom serialization in JSONRenderer without abusing __repr__.
- Enhance Twisted support by offering JSONification of non-structlog log entries.
- PrintLogger now uses proper I/O routines and is thus viable not only for examples but also for production.
- Add `key_order` option to KeyValueRenderer for more predictable log entries with any dict class.


0.1.0 (2013-09-12)
^^^^^^^^^^^^^^^^^^

- Initial release.
