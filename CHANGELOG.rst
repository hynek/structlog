Changelog
=========

Versions are year-based with a strict backward compatibility policy.
The third digit is only for regressions.


16.1.0 (2016-05-24)
-------------------

Backward-incompatible changes:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Python 3.3 and 2.6 aren't supported anymore.
  They may work by chance but any effort to keep them working has ceased.

  The last Python 2.6 release was on October 29, 2013 and isn't supported by the CPython core team anymore.
  Major Python packages like Django and Twisted dropped Python 2.6 a while ago already.

  Python 3.3 never had a significant user base and wasn't part of any distribution's LTS release.

Changes:
^^^^^^^^

- Add a ``drop_missing`` argument to ``KeyValueRenderer``.
  If ``key_order`` is used and a key is missing a value, it's not rendered at all instead of being rendered as ``None``.
  `#67 <https://github.com/hynek/structlog/pull/67>`_
- Exceptions without a ``__traceback__`` are now also rendered on Python 3.
- Don't cache loggers in lazy proxies returned from ``get_logger()``.
  This lead to in-place mutation of them if used before configuration which in turn lead to the problem that configuration was applied only partially to them later.
  `#72 <https://github.com/hynek/structlog/pull/72>`_


----


16.0.0 (2016-01-28)
-------------------

Changes:
^^^^^^^^

- ``structlog.processors.ExceptionPrettyPrinter`` and ``structlog.processors.format_exc_info`` now support passing of Exceptions on Python 3.
- Clean up the context when exiting ``structlog.threadlocal.tmp_bind`` in case of exceptions.
  `#64 <https://github.com/hynek/structlog/issues/64>`_
- Be more more lenient about missing ``__name__``\ s.
  `#62 <https://github.com/hynek/structlog/pull/62>`_
- Add ``structlog.dev.ConsoleRenderer`` that renders the event dictionary aligned and with colors.
- Use `six <https://pythonhosted.org/six/>`_ for compatibility.
- Add ``structlog.processors.UnicodeDecoder`` that will decode all byte string values in an event dictionary to Unicode.
- Add ``serializer`` parameter to ``structlog.processors.JSONRenderer`` which allows for using different (possibly faster) JSON encoders than the standard library.


----


15.3.0 (2015-09-25)
-------------------

Changes:
^^^^^^^^

- Tolerate frames without a ``__name__``, better.
  `#58 <https://github.com/hynek/structlog/pull/58>`_
- Officially support Python 3.5.
- Add ``structlog.ReturnLogger.failure`` and ``structlog.PrintLogger.failure`` as preparation for the new Twisted logging system.


----


15.2.0 (2015-06-10)
-------------------

Changes:
^^^^^^^^

- Allow empty lists of processors.
  This is a valid use case since `#26 <https://github.com/hynek/structlog/issues/26>`_ has been merged.
  Before, supplying an empty list resulted in the defaults being used.
- Prevent Twisted's ``log.err`` from quoting strings rendered by ``structlog.twisted.JSONRenderer``.
- Better support of ``logging.Logger.exception`` within ``structlog``.
  `#52 <https://github.com/hynek/structlog/pull/52>`_
- Add option to specify target key in ``structlog.processors.TimeStamper`` processor.
  `#51 <https://github.com/hynek/structlog/pull/51>`_


----


15.1.0 (2015-02-24)
-------------------

Changes:
^^^^^^^^

- Tolerate frames without a ``__name__``.


----


15.0.0 (2015-01-23)
-------------------

Changes:
^^^^^^^^

- Add ``structlog.stdlib.add_log_level`` and ``structlog.stdlib.add_logger_name`` processors.
  `#44 <https://github.com/hynek/structlog/pull/44>`_
- Add ``structlog.stdlib.BoundLogger.log``.
  `#42 <https://github.com/hynek/structlog/pull/42>`_
- Pass positional arguments to stdlib wrapped loggers that use string formatting.
  `#19 <https://github.com/hynek/structlog/pull/19>`_
- ``structlog`` is now dually licensed under the `Apache License, Version 2 <http://choosealicense.com/licenses/apache/>`_ and the `MIT <http://choosealicense.com/licenses/mit/>`_ license.
  Therefore it is now legal to use structlog with `GPLv2 <http://choosealicense.com/licenses/gpl-2.0/>`_-licensed projects.
  `#28 <https://github.com/hynek/structlog/pull/28>`_
- Add ``structlog.stdlib.BoundLogger.exception``.
  `#22 <https://github.com/hynek/structlog/pull/22>`_


----


0.4.2 (2014-07-26)
------------------

Changes:
^^^^^^^^

- Fixed a memory leak in greenlet code that emulates thread locals.
  It shouldn't matter in practice unless you use multiple wrapped dicts within one program that is rather unlikely.
  `#8 <https://github.com/hynek/structlog/pull/8>`_
- ``structlog.PrintLogger`` now is thread-safe.
- Test Twisted-related code on Python 3 (with some caveats).
- Drop support for Python 3.2.
  There is no justification to add complexity for a Python version that nobody uses.
  If you are one of the `0.350% <https://alexgaynor.net/2014/jan/03/pypi-download-statistics/>`_ that use Python 3.2, please stick to the 0.4 branch; critical bugs will still be fixed.
- Officially support Python 3.4.
- Allow final processor to return a dictionary.
  See the adapting chapter.
  `#26`_
- ``from structlog import *`` works now (but you still shouldn't use it).


----


0.4.1 (2013-12-19)
------------------

Changes:
^^^^^^^^

- Don't cache proxied methods in ``structlog.threadlocal._ThreadLocalDictWrapper``.
  This doesn't affect regular users.
- Various doc fixes.


----


0.4.0 (2013-11-10)
------------------


Backward-incompatible changes:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Changes:
^^^^^^^^

- Add ``structlog.processors.StackInfoRenderer`` for adding stack information to log entries without involving exceptions.
  Also added it to default processor chain.
  `#6 <https://github.com/hynek/structlog/pull/6>`_
- Allow optional positional arguments for ``structlog.get_logger`` that are passed to logger factories.
  The standard library factory uses this for explicit logger naming.
  `#12 <https://github.com/hynek/structlog/pull/12>`_
- Add ``structlog.processors.ExceptionPrettyPrinter`` for development and testing when multiline log entries aren't just acceptable but even helpful.
- Allow the standard library name guesser to ignore certain frame names.
  This is useful together with frameworks.
- Add meta data (e.g. function names, line numbers) extraction for wrapped stdlib loggers.
  `#5 <https://github.com/hynek/structlog/pull/5>`_


----


0.3.2 (2013-09-27)
------------------

Changes:
^^^^^^^^

- Fix stdlib's name guessing.


----


0.3.1 (2013-09-26)
------------------

Changes:
^^^^^^^^

- Add forgotten ``structlog.processors.TimeStamper`` to API documentation.


----


0.3.0 (2013-09-23)
------------------

Changes:
^^^^^^^^

- Greatly enhanced and polished the documentation and added a new theme based on Write The Docs, requests, and Flask.
- Add Python Standard Library-specific BoundLogger that has an explicit API instead of intercepting unknown method calls.
  See ``structlog.stdlib.BoundLogger``.
- ``structlog.ReturnLogger`` now allows arbitrary positional and keyword arguments.
- Add Twisted-specific BoundLogger that has an explicit API instead of intercepting unknown method calls.
  See ``structlog.twisted.BoundLogger``.
- Allow logger proxies that are returned by ``structlog.get_logger`` and ``structlog.wrap_logger`` to cache the BoundLogger they assemble according to configuration on first use.
  See the chapter on performance and the ``cache_logger_on_first_use`` argument of ``structlog.configure`` and ``structlog.wrap_logger``.
- Extract a common base class for loggers that does nothing except keeping the context state.
  This makes writing custom loggers much easier and more straight-forward.
  See ``structlog.BoundLoggerBase``.


----


0.2.0 (2013-09-17)
------------------

Changes:
^^^^^^^^

- Promote to stable, thus henceforth a strict backward compatibility policy is put into effect.
- Add ``key_order`` option to ``structlog.processors.KeyValueRenderer`` for more predictable log entries with any ``dict`` class.
- ``structlog.PrintLogger`` now uses proper I/O routines and is thus viable not only for examples but also for production.
- Enhance Twisted support by offering JSONification of non-structlog log entries.
- Allow for custom serialization in ``structlog.twisted.JSONRenderer`` without abusing ``__repr__``.


----


0.1.0 (2013-09-16)
------------------

Initial release.
