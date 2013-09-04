structlog: Structured Python Logging
====================================

.. image:: https://travis-ci.org/hynek/structlog.png?branch=master
   :target: https://travis-ci.org/hynek/structlog

.. image:: https://coveralls.io/repos/hynek/structlog/badge.png?branch=master
    :target: https://coveralls.io/r/hynek/structlog?branch=master




structlog makes `structured logging <http://journal.paul.querna.org/articles/2011/12/26/log-for-machines-in-json/>`_ easy in Python with *any* underlying logger.
It's licensed under the permissive `Apache License, version 2 <http://choosealicense.com/licenses/apache/>`_, available from `PyPI <https://pypi.python.org/pypi/structlog/>`_, and the source code can be found on `GitHub <https://github.com/hynek/structlog>`_.
The full documentation is on `Read the Docs <https://structlog.readthedocs.org>`_.

structlog targets Python 2.6, 2.7, 3.2, and 3.3 as well PyPy with no additional dependencies for core functionality.

Motivation
----------

Structured logging means that you don’t write hard-to-parse and hard-to-keep-consistent prose in your logs but that you log *events* that happen in a *context* instead.
Effectively all you'll care about is to build a context as you go (e.g. if a user logs in, you bind the user name to your current logger) and log events when they happen (i.e. the user does something log-worthy):

.. code-block:: pycon

   >>> # stdlib logging boilerplate
   >>> import logging, sys
   >>> logging.basicConfig(stream=sys.stdout, format='%(message)s')
   >>> # Now let's wrap the logger and bind some values.
   >>> from structlog import BoundLogger, KeyValueRenderer
   >>> logger = logging.getLogger('example_logger')
   >>> log = BoundLogger.wrap(logger)
   >>> log = log.bind(user='anonymous', some_key=23)
   >>> # Do some application stuff like user authentication.
   >>> # As result, we have new values to bind to our logger.
   >>> log = log.bind(user='hynek', source='http', another_key=42)
   >>> log.warning('user.logged_in', happy=True)
   some_key=23 user='hynek' source='http' another_key=42 happy=True event='user.logged_in'


This ability to bind values to a logger frees you from using conditionals, closures, or special methods to log out all relevant data.

Additionally, structlog offers you a simple but flexible way to *filter* and *modify* your log entries using so called *processors* once you decide to actually log an event.
The possibilities range from logging in JSON, over counting events as metrics, to dropping log entries triggered by your monitoring system.

You can start using structlog *today*, because:

* Events are free-form and interpreted as strings by default.
  Therefore the transition from traditional to structured logging one is seamless most of the time.
  Just start wrapping your logger of choice and bind values later.
  In the worst case you'll have to write some simple adapter.
* You can use both bare logging and structlog at once.
  structlog avoids monkeypatching so a peaceful co-existence between various loggers is unproblematic.

For more information please refer to the `package documentation <https://structlog.readthedocs.org>`_.

.. image:: https://d2weczhvl823v0.cloudfront.net/hynek/structlog/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free
