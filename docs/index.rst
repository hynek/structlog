structlog: Structured Logging in Python
=======================================

Release v\ |version| (:ref:`Installation <install>`).

.. include:: intro.rst
   :start-after: :orphan:


Why You Want to Use structlog
-----------------------------

Structured logging means that you don’t write hard-to-parse and hard-to-keep-consistent prose in your logs but that you log *events* that happen in a *context* instead.
All you'll care about is to build a context as you go (e.g. if a user logs in, you bind their user name to your current logger) and log events when they happen (i.e. the user does something log-worthy):

.. literalinclude:: code_examples/teaser.txt
   :language: pycon
   :start-after: log =


This ability to bind key/values pairs to a logger frees you from using conditionals, closures, or boilerplate methods to log out all relevant data.

Additionally, structlog offers you a simple but flexible way to *filter* and *modify* your log entries using so called :ref:`processors <processors>` once you decide to actually log an event.
The possibilities include logging in JSON, adding arbitrary meta data, counting events as metrics, or dropping log entries caused by your monitoring system.


Why You Can Start Using structlog TODAY
---------------------------------------

- You can use both bare logging and structlog at once.
  structlog avoids monkeypatching so a peaceful co-existence between various loggers is unproblematic.
- Events are free-form and interpreted as strings by default.
  Therefore the transition from traditional to structured logging is seamless most of the time.
  Just start wrapping your logger of choice and bind values later.
  In the worst case you'll have to write some simple adapter.
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
