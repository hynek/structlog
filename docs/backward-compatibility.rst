Backward Compatibility
======================

``structlog`` has a very strong backward compatibility policy that is inspired by the one of the `Twisted framework <https://twistedmatrix.com/trac/wiki/CompatibilityPolicy>`_.

Put simply, you shouldn't ever be afraid to upgrade ``structlog`` if you're using its public APIs.
If there will ever be need to break compatibility, it will be announced in the :doc:`changelog` and raise deprecation warning for a year before it's finally really broken.


.. _exemption:

.. warning::

   You cannot however rely on the default settings and the :mod:`structlog.dev` module.
   They may be adjusted in the future to provide a better experience when starting to use ``structlog``.
   So please make sure to **always** properly configure your applications.
