========================================
structlog: Structured Logging for Python
========================================

.. image:: https://pypip.in/version/structlog/badge.svg
   :target: https://pypi.python.org/pypi/structlog/
   :alt: Latest Version

.. image:: https://travis-ci.org/hynek/structlog.svg?branch=master
   :target: https://travis-ci.org/hynek/structlog

.. image:: https://coveralls.io/repos/hynek/structlog/badge.svg?branch=master
    :target: https://coveralls.io/r/hynek/structlog?branch=master

``structlog`` makes structured logging in Python easy by *augmenting* your *existing* logger.
It allows you to split your log entries up into key/value pairs and build them incrementally without annoying boilerplate code.

.. code-block:: pycon

   >>> from structlog import get_logger
   >>> log = get_logger()
   >>> log = log.bind(user='anonymous', some_key=23)
   >>> log = log.bind(user='hynek', another_key=42)
   >>> log.info('user.logged_in', happy=True)
   some_key=23 user='hynek' another_key=42 happy=True event='user.logged_in'

.. begin

It's dual-licensed under `Apache License, version 2 <http://choosealicense.com/licenses/apache/>`_ and `MIT <http://choosealicense.com/licenses/mit/>`_, available from `PyPI <https://pypi.python.org/pypi/structlog/>`_, the source code can be found on `GitHub <https://github.com/hynek/structlog>`_, the documentation at `http://www.structlog.org/ <http://www.structlog.org>`_.

``structlog`` targets Python 2.6, 2.7, 3.3, 3.4, and PyPy with no additional dependencies for core functionality.

If you need any help, visit us on ``#structlog`` on `Freenode <https://freenode.net>`_!
