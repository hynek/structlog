====
Why…
====

…Structured Logging?
====================

      I believe the widespread use of format strings in logging is based on two presumptions:

      - The first level consumer of a log message is a human.
      - The programmer knows what information is needed to debug an issue.

      I believe these presumptions are **no longer correct** in server side software.

      ---`Paul Querna <https://paul.querna.org/articles/2011/12/26/log-for-machines-in-json/>`_

Structured logging means that you don't write hard-to-parse and hard-to-keep-consistent prose in your log.
Instead, you log *events* that happen in a *context* of key/value pairs.


…structlog?
===========

.. include:: ../README.rst
   :start-after: -begin-spiel-
   :end-before: -end-spiel-
