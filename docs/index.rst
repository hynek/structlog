=============================
Structured Logging for Python
=============================

Release v\ |version| (:doc:`What's new? <changelog>`).

.. include:: ../README.rst
   :start-after: begin

The Pitch
=========

``structlog`` makes structured logging with *key-value logging*, *incremental context building* and *arbitrary formatting* as easy as:

.. doctest::

   >>> from structlog import get_logger
   >>> log = get_logger()
   >>> log = log.bind(user='anonymous', some_key=23)
   >>> log = log.bind(user='hynek', another_key=42)
   >>> log.info('user.logged_in', happy=True)
   some_key=23 user='hynek' another_key=42 happy=True event='user.logged_in'

Please note that this example does *not* use standard library logging (but could so :ref:`easily <standard-library-lite>`).
The logger that's returned by :func:`~structlog.get_logger()` is *freely* :doc:`configurable <configuration>` and uses a simple :class:`~structlog.PrintLogger` by default.



For…

- …reasons why structured logging in general and ``structlog`` in particular are the way to go, consult :doc:`why`.
- …more realistic examples, peek into  :doc:`examples`.
- …getting started right away, jump straight into :doc:`getting-started`.

Since ``structlog`` avoids monkey-patching and events are fully free-form, you can start using it **today**!

User's Guide
============

Basics
------

.. toctree::
   :maxdepth: 1

   why
   getting-started
   loggers
   configuration
   thread-local
   processors
   examples
   development
   faq


Integration with Existing Systems
---------------------------------

``structlog`` can be used immediately with *any* existing logger.
However it comes with special wrappers for the Python standard library and Twisted that are optimized for their respective underlying loggers and contain less magic.

.. toctree::
   :maxdepth: 2

   standard-library
   twisted
   logging-best-practices


Advanced Topics
---------------

.. toctree::
   :maxdepth: 1

   custom-wrappers
   performance


Project Information
===================

.. toctree::
   :maxdepth: 1

   backward-compatibility
   contributing
   license
   changelog


API Reference
=============

.. toctree::
   :maxdepth: 4

   api


Indices and tables
==================

- :ref:`genindex`
- :ref:`modindex`
- :ref:`search`
