Types
=====

Static types are an excellent way to make your code more robust, self-documenting, and maintainable in the long run.
And as of 20.2.0, ``structlog`` comes with type hints for all its APIs.

Since ``structlog`` is highly configurable and tries to give a clean facade to its users, adding types without breaking compatibility while remaining useful was a formidable task.

If you used ``structlog`` and mypy before 20.2.0, you will probably find that mypy is failing now.
As a quick fix, add the following lines into your ``mypy.ini`` that should be at the root of your project directory (and must start with a ``[mypy]`` section):

.. code:: ini

   [mypy-structlog.*]
   follow_imports=skip

It will ignore ``structlog``'s type stubs until you're ready to adapt your code base to them.


----

The main problem is that `structlog.get_logger()` returns whatever you've configured the bound logger to be.
The only commonality are the binding methods like ``bind()``.
We've extracted that into the `structlog.types.BindableLogger` `typing.Protocol`.

The second problem is that said ``bind()`` and its cousins are inherited from a common base class (a `big <https://www.youtube.com/watch?v=3MNVP9-hglc>`_ `mistake <https://python-patterns.guide/gang-of-four/composition-over-inheritance/>`_ in hindsight) and can't know what concrete class subclasses them and therefore what type they are returning.

The chosen solution is adding `structlog.stdlib.get_logger()` that just calls `structlog.get_logger()` but has the correct type hints and adding `structlog.stdlib.BoundLogger.bind` et al that also only delegate to the base class.

Rather sooner than later, the concept of the base class will be replaced by proper delegation that will put the context-related methods into a proper class (with proxy stubs for backward compatibility).
In the end, we're already delegating anyway.
