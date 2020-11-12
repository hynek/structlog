Type Hints
==========

Static type hints -- together with a type checker like `Mypy <https://mypy.readthedocs.io/en/stable/>`_ -- are an excellent way to make your code more robust, self-documenting, and maintainable in the long run.
And as of 20.2.0, ``structlog`` comes with type hints for all of its APIs.

Since ``structlog`` is highly configurable and tries to give a clean facade to its users, adding types without breaking compatibility, while remaining useful was a formidable task.

If you used ``structlog`` and Mypy before 20.2.0, you will probably find that Mypy is failing now.
As a quick fix, add the following lines into your ``mypy.ini`` that should be at the root of your project directory (and must start with a ``[mypy]`` section):

.. code:: ini

   [mypy-structlog.*]
   follow_imports = skip

It will ignore ``structlog``'s type stubs until you're ready to adapt your code base to them.


----

The main problem is that `structlog.get_logger()` returns whatever you've configured the bound logger to be.
The only commonality are the binding methods like ``bind()`` and we've extracted them into the `structlog.types.BindableLogger` :class:`~typing.Protocol`.
But using that as a return type is worse than useless, because you'd have to use `typing.cast` on every logger returned by `structlog.get_logger()`, if you wanted to actually call any logging methods.

The second problem is that said ``bind()`` and its cousins are inherited from a common base class (a `big <https://www.youtube.com/watch?v=3MNVP9-hglc>`_ `mistake <https://python-patterns.guide/gang-of-four/composition-over-inheritance/>`_ in hindsight) and can't know what concrete class subclasses them and therefore what type they are returning.

The chosen solution is adding `structlog.stdlib.get_logger()` that just calls `structlog.get_logger()` but has the correct type hints and adding `structlog.stdlib.BoundLogger.bind` et al that also only delegate to the base class.

`structlog.get_logger()` is typed as returning `typing.Any` so you can use your own type annotation and stick to the old APIs, if that's what you prefer:

.. code::

   import structlog

   logger: structlog.stdlib.BoundLogger = structlog.get_logger()
   logger.info("hi")  # <- ok
   logger.msg("hi")   # <- mypy: 'error: "BoundLogger" has no attribute "msg"'

----

Rather sooner than later, the concept of the base class will be replaced by proper delegation that will put the context-related methods into a proper class (with proxy stubs for backward compatibility).
In the end, we're already delegating anyway.
