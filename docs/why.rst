Why…
====

…Structured Logging?
---------------------

      I believe the widespread use of format strings in logging is based on two presumptions:

      - The first level consumer of a log message is a human.
      - The programmer knows what information is needed to debug an issue.

      I believe these presumptions are **no longer correct** in server side software.

      ---`Paul Querna <https://journal.paul.querna.org/articles/2011/12/26/log-for-machines-in-json/>`_

Structured logging means that you don't write hard-to-parse and hard-to-keep-consistent prose in your logs but that you log *events* that happen in a *context* instead.


…structlog?
------------

Because it's easy and you don't have to replace your underlying logger -- you just add structure to your log entries and format them to strings before they hit your real loggers.

``structlog`` supports you with accepting key-value pairs as arguments, building your context as you go (e.g. if a user logs in, you bind their user name to your current logger) and log events when they happen (i.e. the user does something log-worthy):

.. doctest::

   >>> from structlog import get_logger
   >>> log = get_logger()
   >>> log = log.bind(user='anonymous', some_key=23)
   >>> log = log.bind(user='hynek', another_key=42)
   >>> log.info('user.logged_in', happy=True)
   some_key=23 user='hynek' another_key=42 happy=True event='user.logged_in'

This ability to bind key/values pairs to a logger frees you from using conditionals, closures, or boilerplate methods to log out all relevant data.

Additionally, ``structlog`` offers you a flexible way to *filter* and *modify* your log entries using so called :ref:`processors <processors>` before the entry is passed to your real logger.
The possibilities include :class:`logging in JSON <structlog.processors.JSONRenderer>`, adding arbitrary meta data like :class:`timestamps <structlog.processors.TimeStamper>`, counting events as metrics, or :ref:`dropping log entries <cond_drop>` caused by your monitoring system.
``structlog`` is also flexible enough to allow transparent :ref:`thread local <threadlocal>` storage for your context if you don't like the idea of local bindings as in the example above.
