Types
=====

Static types are an excellent way to make your code more robust, self-documenting, and maintainable in the long run.
And as of 20.2.0, ``structlog`` comes with type hints for all its APIs.

Since ``structlog`` is highly configurable and tries to give a clean facade to its users, adding types without breaking compatibility while remaining useful was a formidable task.

If you used ``structlog`` and mypy before 20.2.0, you will probably find that mypy is failing now.
As a quick fix, add the following lines into your ``mypy.ini`` that should be at the root of your project directory (and must start with a ``[mypy]``):

.. code:: ini

   [mypy-structlog.*]
   follow_imports=skip

It will ignore ``structlog``'s type stubs until you're ready to adapt your code base to them.
