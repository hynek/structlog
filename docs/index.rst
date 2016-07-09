=============================
Structured Logging for Python
=============================

Release v\ |version| (:doc:`What's new? <changelog>`).

.. include:: ../README.rst
   :start-after: begin
   :end-before: -end-


User's Guide
============


Basics
------

.. toctree::
   :maxdepth: 2

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


API Reference
=============

.. toctree::
   :maxdepth: 4

   api


.. include:: ../README.rst
   :start-after: -end-

.. toctree::
   :maxdepth: 1

   backward-compatibility
   contributing
   license
   changelog


Indices and tables
==================

- :ref:`genindex`
- :ref:`modindex`
- :ref:`search`
