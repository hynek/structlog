# Type Hints

Static type hints -- together with a type checker like [*Mypy*](https://mypy.readthedocs.io/en/stable/) -- are an excellent way to make your code more robust, self-documenting, and maintainable in the long run.
And as of 20.2.0, *structlog* comes with type hints for all of its APIs.

Since *structlog* is highly configurable and tries to give a clean façade to its users, adding types without breaking compatibility -- while remaining useful! -- was a formidable task.

---

The main problem is that `structlog.get_logger()` returns whatever you've configured the *bound logger* to be.
The only commonality are the binding methods like `bind()` and we've extracted them into the {class}`structlog.typing.BindableLogger` {class}`~typing.Protocol`.
But using that as a return type is worse than useless, because you'd have to use {func}`typing.cast` on every logger returned by `structlog.get_logger()`, if you wanted to actually call any logging methods.

The second problem is that said `bind()` and its cousins are inherited from a common base class (a [big](https://www.youtube.com/watch?v=3MNVP9-hglc) [mistake](https://python-patterns.guide/gang-of-four/composition-over-inheritance/) in hindsight) and can't know what concrete class subclasses them and therefore what type they are returning.

The chosen solution is adding {func}`structlog.stdlib.get_logger()` that just calls `structlog.get_logger()` but has the correct type hints and adding `structlog.stdlib.BoundLogger.bind` et al that also only delegate to the base class.

`structlog.get_logger()` is typed as returning {any}`typing.Any` so you can use your own type annotation and stick to the old APIs, if that's what you prefer:

```
import structlog

logger: structlog.stdlib.BoundLogger = structlog.get_logger()
logger.info("hi")  # <- ok
logger.msg("hi")   # <- Mypy: 'error: "BoundLogger" has no attribute "msg"'
```
