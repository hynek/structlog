structlog: Structured Logging in Python
=======================================

Release v\ |version| (:doc:`What's new? <changelog>`).

.. include:: intro.rst
   :start-after: :orphan:


Why You Want Structured Logging
-------------------------------

      I believe the widespread use of format strings in logging is based on two presumptions:

      - The first level consumer of a log message is a human.
      - The programmer knows what information is needed to debug an issue.

      I believe these presumptions are **no longer correct** in server side software.

      ---`Paul Querna <http://journal.paul.querna.org/articles/2011/12/26/log-for-machines-in-json/>`_

Structured logging means that you don't write hard-to-parse and hard-to-keep-consistent prose in your logs but that you log *events* that happen in a *context* instead.


Why structlog?
--------------

Because it's easy and you don't have to replace your underlying logger -- you just add structure to your log entries and format them to strings before they hit your real loggers.

structlog supports you with building your context as you go (e.g. if a user logs in, you bind their user name to your current logger) and log events when they happen (i.e. the user does something log-worthy):

.. doctest::

   >>> from structlog import get_logger
   >>> log = get_logger()
   >>> log = log.bind(user='anonymous', some_key=23)
   >>> log = log.bind(user='hynek', another_key=42)
   >>> log.info('user.logged_in', happy=True)
   some_key=23 user='hynek' another_key=42 happy=True event='user.logged_in'

This ability to bind key/values pairs to a logger frees you from using conditionals, closures, or boilerplate methods to log out all relevant data.

Additionally, structlog offers you a flexible way to *filter* and *modify* your log entries using so called :ref:`processors <processors>` before the entry is passed to your real logger.
The possibilities include :class:`logging in JSON <structlog.processors.JSONRenderer>`, adding arbitrary meta data like :class:`timestamps <structlog.processors.TimeStamper>`, counting events as metrics, or :ref:`dropping log entries <cond_drop>` caused by your monitoring system.
structlog is also flexible enough to allow transparent :ref:`thread local <threadlocal>` storage for your context if you don't like the idea of local bindings as in the example above.

Since structlog avoids monkey-patching and events are fully free-form, you can start using it **today**!

Intrigued? :ref:`Get started now <getting-started>` or have a look at more realistic :ref:`examples <examples>` and be completely convinced!


User's Guide
------------


Basics
^^^^^^

.. toctree::
   :maxdepth: 2

   getting-started
   loggers
   configuration
   thread-local
   processors
   examples


Integration with Existing Systems
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

structlog can be used immediately with any existing logger.
However it comes with special wrappers for the Python standard library and Twisted that are optimized for their respective underlying loggers and contain less guesswork and magic.

.. toctree::
   :maxdepth: 2

   standard-library
   twisted
   logging-best-practices


Advanced Topics
^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 2

   custom-wrappers
   performance


API
---

.. toctree::
   :maxdepth: 4

   api

Additional Notes
----------------

.. toctree::
   :maxdepth: 1

   contributing
   license
   changelog


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
