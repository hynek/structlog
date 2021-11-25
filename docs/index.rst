=============================
Structured Logging for Python
=============================

Release v\ |version| (`What's new? <changelog>`).

.. include:: ../README.rst
   :start-after: -begin-short-
   :end-before: -end-short-


First steps:

- If you're not sure whether ``structlog`` is for you, have a look at `why`.
- If you can't wait to log your first entry, start at `getting-started` and then work yourself through the basic docs.
- Once you have basic grasp of how ``structlog`` works, acquaint yourself with the `integrations <#integration-with-existing-systems>`_ ``structlog`` is shipping with.


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
   testing
   thread-local
   contextvars
   processors
   examples
   development
   types


Integration with Existing Systems
---------------------------------

``structlog`` can be used immediately with *any* existing logger.
However it comes with special wrappers for the Python standard library and Twisted that are optimized for their respective underlying loggers and contain less magic.

.. toctree::
   :maxdepth: 1

   standard-library
   twisted
   logging-best-practices


Advanced Topics
---------------

.. toctree::
   :maxdepth: 1

   custom-wrappers
   performance


API Reference
=============

.. toctree::
   :maxdepth: 4

   api


.. include:: ../README.rst
   :start-after: -begin-meta-

.. toctree::
   :maxdepth: 1

   license
   changelog


Indices and tables
==================

- `genindex`
- `modindex`
- `search`
