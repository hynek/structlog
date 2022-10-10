=========
structlog
=========

*Simple. Powerful. Fast. Pick three.*

Release |release| (`What's new? <changelog>`)

.. include:: ../README.md
   :parser: myst_parser.sphinx_
   :start-after: <!-- begin-short -->
   :end-before: <!-- end-short -->


First Steps
===========

- If you're not sure whether ``structlog`` is for you, have a look at `why`.
- If you can't wait to log your first entry, start at `getting-started` and then work yourself through our tutorial.
- Once you have basic grasp of how ``structlog`` works, acquaint yourself with the `integrations <#integration-with-existing-systems>`_ ``structlog`` is shipping with.


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
   processors
   contextvars
   examples
   development
   testing
   types


Integration with Existing Systems
---------------------------------

``structlog`` can be used immediately with *any* existing logger, or with the one with that it ships.
However it comes with special wrappers for the Python standard library and Twisted that are optimized for their respective underlying loggers and contain less magic.

.. toctree::
   :maxdepth: 2

   frameworks
   standard-library
   twisted


Advanced Topics
---------------

.. toctree::
   :maxdepth: 2

   logging-best-practices
   performance
   custom-wrappers


Deprecated Features
-------------------

.. toctree::
   :maxdepth: 1

   thread-local


API Reference
=============

.. toctree::
   :maxdepth: 2

   api


Project Information
===================

.. include:: ../README.md
   :parser: myst_parser.sphinx_
   :start-after: ## Project Information


.. stop Sphinx from complaints about orphaned docs, we link them elsewhere
.. toctree::
   :hidden:

   license
   changelog


Indices and tables
==================

- `genindex`
- `modindex`
