.. image:: http://www.structlog.org/en/latest/_static/structlog_logo_small.png
   :alt: structlog Logo
   :width: 256px
   :target: http://www.structlog.org/

``structlog``: Structured Logging for Python
============================================

.. image:: https://readthedocs.org/projects/structlog/badge/?version=stable
   :target: https://structlog.readthedocs.io/en/stable/?badge=stable
   :alt: Documentation Status

.. image:: https://travis-ci.org/hynek/structlog.svg?branch=master
   :target: https://travis-ci.org/hynek/structlog

.. image:: https://codecov.io/github/hynek/structlog/branch/master/graph/badge.svg
  :target: https://codecov.io/github/hynek/structlog
  :alt: Test Coverage

.. image:: https://www.irccloud.com/invite-svg?channel=%23structlog&amp;hostname=irc.freenode.net&amp;port=6697&amp;ssl=1
   :target: https://www.irccloud.com/invite?channel=%23structlog&amp;hostname=irc.freenode.net&amp;port=6697&amp;ssl=1

.. -begin-short-

``structlog`` makes logging in Python less painful and more powerful by adding structure to your log entries.

It's up to you whether you want ``structlog`` to take care about the **output** of your log entries or whether you prefer to **forward** them to an existing logging system like the standard library's ``logging`` module.

.. -end-short-


.. -begin-spiel-

Easier Logging
--------------

You can stop writing prose and start thinking in terms of an event that happens in the context of key/value pairs:

.. code-block:: pycon

   >>> from structlog import get_logger
   >>> log = get_logger()
   >>> log.info("key_value_logging", out_of_the_box=True, effort=0)
   2016-04-20 16:20.13 key_value_logging              effort=0 out_of_the_box=True

Each log entry is a meaningful dictionary instead of an opaque string now!


Data Binding
------------

Since log entries are dictionaries, you can start binding and re-binding key/value pairs to your loggers to ensure they are present in every following logging call:

.. code-block:: pycon

   >>> log = log.bind(user="anonymous", some_key=23)
   >>> log = log.bind(user="hynek", another_key=42)
   >>> log.info("user.logged_in", happy=True)
   2016-04-20 16:20.13 user.logged_in                 another_key=42 happy=True some_key=23 user='hynek'


Powerful Pipelines
------------------

Each log entry goes through a `processor pipeline <http://www.structlog.org/en/stable/processors.html>`_ that is just a chain of functions that receive a dictionary and return a new dictionary that gets fed into the next function.
That allows for simple but powerful data manipulation:

.. code-block:: python

   def timestamper(logger, log_method, event_dict):
       """Add a timestamp to each log entry."""
       event_dict["timestamp"] = time.time()
       return event_dict

There are `plenty of processors <http://www.structlog.org/en/stable/api.html#module-structlog.processors>`_ for most common tasks coming with ``structlog``:

- Collectors of `call stack information <http://www.structlog.org/en/stable/api.html#structlog.processors.StackInfoRenderer>`_ ("How did this log entry happen?"),
- …and `exceptions <http://www.structlog.org/en/stable/api.html#structlog.processors.format_exc_info>`_ ("What happened‽").
- Unicode encoders/decoders.
- Flexible `timestamping <http://www.structlog.org/en/stable/api.html#structlog.processors.TimeStamper>`_.



Formatting
----------

``structlog`` is completely flexible about *how* the resulting log entry is emitted.
Since each log entry is a dictionary, it can be formatted to **any** format:

- A colorful key/value format for `local development <http://www.structlog.org/en/stable/development.html>`_,
- `JSON <http://www.structlog.org/en/stable/api.html#structlog.processors.JSONRenderer>`_ for easy parsing,
- or some standard format you have parsers for like nginx or Apache httpd.

Internally, formatters are processors whose return value (usually a string) is passed into loggers that are responsible for the output of your message.
``structlog`` comes with multiple useful formatters out of-the-box.


Output
------

``structlog`` is also very flexible with the final output of your log entries:

- A **built-in** lightweight printer like in the examples above.
  Easy to use and fast.
- Use the **standard library**'s or **Twisted**'s logging modules for compatibility.
  In this case ``structlog`` works like a wrapper that formats a string and passes them off into existing systems that won't ever know that ``structlog`` even exists.
  Or the other way round: ``structlog`` comes with a ``logging`` formatter that allows for processing third party log records.
- Don't format it to a string at all!
  ``structlog`` passes you a dictionary and you can do with it whatever you want.
  Reported uses cases are sending them out via network or saving them in a database.

.. -end-spiel-


Project Information
-------------------

.. -begin-meta-

``structlog`` is dual-licensed under `Apache License, version 2 <https://choosealicense.com/licenses/apache/>`_ and `MIT <https://choosealicense.com/licenses/mit/>`_, available from `PyPI <https://pypi.org/project/structlog/>`_, the source code can be found on `GitHub <https://github.com/hynek/structlog>`_, the documentation at http://www.structlog.org/.

``structlog`` targets Python 2.7, 3.4 and newer, and PyPy.

If you need any help, visit us on ``#structlog`` on `Freenode <https://freenode.net>`_!
