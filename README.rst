========================================
structlog: Structured Logging for Python
========================================

.. image:: https://pypip.in/version/structlog/badge.svg
   :target: https://pypi.python.org/pypi/structlog/
   :alt: Latest Version

.. image:: https://travis-ci.org/hynek/structlog.png?branch=master
   :target: https://travis-ci.org/hynek/structlog

.. image:: https://coveralls.io/repos/hynek/structlog/badge.png?branch=master
    :target: https://coveralls.io/r/hynek/structlog?branch=master

.. begin-intro

``structlog`` makes structured logging in Python easy by *augmenting* your *existing* logger.
It allows you to split your log entries up into key/value pairs and build them incrementally without annoying boilerplate code.

It's dual-licensed under `Apache License, version 2 <http://choosealicense.com/licenses/apache/>`_ and `MIT <http://choosealicense.com/licenses/mit/>`_, available from `PyPI <https://pypi.python.org/pypi/structlog/>`_, the source code can be found on `GitHub <https://github.com/hynek/structlog>`_, the documentation at `http://www.structlog.org/ <http://www.structlog.org>`_.

``structlog`` targets Python 2.6, 2.7, 3.3, 3.4, and PyPy with no additional dependencies for core functionality.

If you need any help, visit us on ``#structlog`` on `Freenode <http://freenode.net>`_!


The Pitch
=========

``structlog`` makes structured logging with *incremental context building* and *arbitrary formatting* as easy as:

.. code-block:: pycon

   >>> from structlog import get_logger
   >>> log = get_logger()
   >>> log = log.bind(user='anonymous', some_key=23)
   >>> log = log.bind(user='hynek', another_key=42)
   >>> log.info('user.logged_in', happy=True)
   some_key=23 user='hynek' another_key=42 happy=True event='user.logged_in'

.. end-intro

It does *not* rely on any specific logging library and comes with direct support for standard library’s ``logging`` module and Twisted.
