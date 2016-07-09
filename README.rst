========================================
structlog: Structured Logging for Python
========================================

.. image:: https://travis-ci.org/hynek/structlog.svg?branch=master
   :target: https://travis-ci.org/hynek/structlog

.. image:: https://codecov.io/github/hynek/structlog/coverage.svg?branch=master
   :target: https://codecov.io/github/hynek/structlog?branch=master

.. image:: https://www.irccloud.com/invite-svg?channel=%23structlog&amp;hostname=irc.freenode.net&amp;port=6697&amp;ssl=1
   :target: https://www.irccloud.com/invite?channel=%23structlog&amp;hostname=irc.freenode.net&amp;port=6697&amp;ssl=1

.. begin

``structlog`` makes structured logging in Python easy by either *augmenting* your *existing* logger if you need interoperability or supplying you with a lightweight logging layer if you want *performance* and *simplicity*.


Easier Logging
==============

You will immediately appreciate the convenience of key/value-based logging:

.. code-block:: pycon

   >>> from structlog import get_logger
   >>> log = get_logger()
   >>> log.info("key_value_logging", out_of_the_box=True, effort=0)
   out_of_the_box=True effort=0 event='key_value_logging'

Never ponder on how to phrase a log message again!


Data Binding
============

If you wish to, you can also bind key/value-pairs to loggers that get added automatically to all following loging calls:

.. code-block:: pycon

   >>> log = log.bind(user="anonymous", some_key=23)
   >>> log = log.bind(user="hynek", another_key=42)
   >>> log.info("user.logged_in", happy=True)
   some_key=23 user='hynek' another_key=42 happy=True event='user.logged_in'

Stop repeating yourself and still never forget an important piece of unformation in a log entry again!

Please note that those examples do *not* use standard library logging (but `could so <http://www.structlog.org/en/stable/standard-library.html>`_).
The logger that's returned by ``structlog.get_logger()`` is *freely* `configurable <http://www.structlog.org/en/stable/configuration.html>`_ and uses a simple but effective `structlog.PrintLogger <http://www.structlog.org/en/stable/api.html#structlog.PrintLogger>`_ by default.


Powerful Pipelines
==================

Since the log entries are dictionaries now (instead of unstructured prose strings), they allow for simple yet powerful `processor pipelines <http://www.structlog.org/en/stable/processors.html>`_ of callables that receive a dictionary and return a new one:

.. code-block:: python

   def timestamper(logger, log_method, event_dict):
       """Add a timestamp to each log entry."""
       event_dict["timestamp"] = calendar.timegm(time.gmtime())
       return event_dict

There are `plenty of processors <http://www.structlog.org/en/stable/api.html#module-structlog.processors>`_ for most common tasks coming with ``structlog``.


Formatting
==========

Finally, structured data is much easier to format into *any* other logging format.
Be it `colorful console output in developement <http://www.structlog.org/en/stable/development.html>`_, imitating the nginx log format, or logging out JSON for parsing and centralized storage.

.. image:: http://www.structlog.org/en/stable/_images/console_renderer.png

Internally, formatters are just processors whose return value is passed into wrapped loggers and ``structlog`` comes with multiple useful formatters out of-the-box.



Since ``structlog`` avoids monkey-patching and events are fully free-form, you can start using it **today**!

.. -end-


Project Information
===================

``structlog`` is dual-licensed under `Apache License, version 2 <http://choosealicense.com/licenses/apache/>`_ and `MIT <http://choosealicense.com/licenses/mit/>`_, available from `PyPI <https://pypi.python.org/pypi/structlog/>`_, the source code can be found on `GitHub <https://github.com/hynek/structlog>`_, the documentation at http://www.structlog.org/.

``structlog`` targets Python 2.7, 3.4 and newer, and PyPy.

If you need any help, visit us on ``#structlog`` on `Freenode <https://freenode.net>`_!
