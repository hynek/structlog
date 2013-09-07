.. _api:

structlog Package
=================

.. module:: structlog

:mod:`structlog` Package
------------------------

.. autofunction:: wrap_logger
.. autofunction:: configure
.. autofunction:: configure_once
.. autofunction:: reset_defaults

.. autoclass:: BoundLogger
   :members: new, bind

.. autoclass:: PrintLogger
.. autoclass:: ReturnLogger

.. autoexception:: DropEvent

:mod:`threadlocal` Module
-------------------------

.. automodule:: structlog.threadlocal
    :members: wrap_dict, tmp_bind
    :undoc-members:
    :show-inheritance:

.. _procs:

:mod:`processors` Module
------------------------

.. automodule:: structlog.processors
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`stdlib` Module
--------------------

.. automodule:: structlog.stdlib
    :members: get_logger, filter_by_level
    :undoc-members:
    :show-inheritance:

:mod:`twisted` Module
---------------------

.. automodule:: structlog.twisted
    :members: get_logger, LogAdapter, JSONRenderer
    :undoc-members:
    :show-inheritance:

