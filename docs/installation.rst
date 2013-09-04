.. _install:

Installation
============

structlog can be easily installed using::

   $ pip install structlog

Python 2.6
----------

If you're running Python 2.6 and want to use ``OrderedDict``\ s for your context (which is the default), you also have to install the respective compatibility package::

   $ pip install ordereddict

If the order of the keys of your context doesn't matter (e.g. if you're logging JSON that gets parsed anyway), simply use a vanilla ``dict`` to avoid this dependency.
See :ref:`configuration` on how to achieve that.
