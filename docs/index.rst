structlog: Structured Logging in Python
=======================================

Release v\ |version| (:ref:`Installation <install>`).

.. include:: intro.rst
   :start-after: :orphan:


Why You Want Structured Logging
-------------------------------

      I believe the widespread use of format strings in logging is based on two presumptions:

      - The first level consumer of a log message is a human.
      - The programer knows what information is needed to debug an issue.

      I believe these presumptions are **no longer correct** in server side software.

      ---`Paul Querna <http://journal.paul.querna.org/articles/2011/12/26/log-for-machines-in-json/>`_

Structured logging means that you don't write hard-to-parse and hard-to-keep-consistent prose in your logs but that you log *events* that happen in a key/value-based *context* instead.


Why You Want to Use structlog
-----------------------------

Because it's easy and you don't have to replace your underlying logger -- you just add structure to your log entries and format them to strings before they hit your real loggers.

structlog supports you with building your context as you go (e.g. if a user logs in, you bind their user name to your current logger) and log events when they happen (i.e. the user does something log-worthy):

.. literalinclude:: code_examples/teaser.txt
   :language: pycon
   :start-after: log =


This ability to bind key/values pairs to a logger frees you from using conditionals, closures, or boilerplate methods to log out all relevant data.

Additionally, structlog offers you a flexible way to *filter* and *modify* your log entries using so called :ref:`processors <processors>` before the entry is passed to your real logger.
The possibilities include :class:`logging in JSON <structlog.processors.JSONRenderer>`, adding arbitrary meta data like :class:`timestamps <structlog.processors.TimeStamper>`, counting events as metrics, or :ref:`dropping log entries <cond_drop>` caused by your monitoring system.


Why You Can Start Using structlog TODAY
---------------------------------------

- You can use both your bare logger and as well as the same logger wrapped by structlog at the same time.
  structlog avoids monkeypatching so a peaceful co-existence between various loggers is unproblematic.
- Events are free-form and interpreted as strings by default.
  Therefore the transition from traditional to structured logging is seamless most of the time.
  Just start wrapping your logger of choice and bind values later.
- If you don't like the idea of keeping the context within a local logger instance like in the example above, structlog offers transparent :ref:`thread local <threadlocal>` storage for your context.

Intrigued? Have a look at more realistic :ref:`examples <examples>` and be completely convinced!

User's Guide
------------

.. toctree::
   :maxdepth: 2

   installation
   getting-started
   loggers
   processors
   examples

API
---

.. toctree::
   :maxdepth: 4

   api

Additional Notes
----------------

.. toctree::
   :maxdepth: 1

   license
   changelog


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
