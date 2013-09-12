.. _api:

structlog Package
=================

.. module:: structlog

:mod:`structlog` Package
------------------------

.. autofunction:: get_logger
.. autofunction:: getLogger
.. autofunction:: wrap_logger
.. autofunction:: configure
.. autofunction:: configure_once
.. autofunction:: reset_defaults

.. autoclass:: BoundLogger
   :members: new, bind, unbind

.. autoclass:: PrintLogger
.. autoclass:: ReturnLogger

.. autoexception:: DropEvent

:mod:`threadlocal` Module
-------------------------

.. automodule:: structlog.threadlocal
    :members: wrap_dict, tmp_bind, as_immutable
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

.. autoclass:: LoggerFactory
   :members: __call__
.. autofunction:: filter_by_level

:mod:`twisted` Module
---------------------

.. automodule:: structlog.twisted

.. autoclass:: LoggerFactory
.. autoclass:: EventAdapter
.. autoclass:: JSONRenderer

