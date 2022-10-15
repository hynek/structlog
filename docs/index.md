# structlog

*Simple. Powerful. Fast. Pick three.*

Release **{sub-ref}`release`**  ([What's new?](changelog))

---

```{eval-rst}
.. include:: ../README.md
   :parser: myst_parser.sphinx_
   :start-after: <!-- begin-short -->
   :end-before: <!-- end-short -->

```

If you’d like more information on why structured logging in general and *structlog* in particular are good ideas, we’ve prepared a [summary](why.md) just for you.
Otherwise, let’s dive right in!

```{toctree}
:hidden: true

why
```


## Basics

The first chapters teach you all you need to use *structlog* productively.
They build gently on each other, so ideally, read them in order.


```{toctree}
:maxdepth: 2

getting-started
bound-loggers
configuration
processors
contextvars
```


## In-Development Affordances

*structlog*'s focus is production systems, but it comes with **pretty console logging** and handy in-development helpers both for your **comfort** and your code's **quality**.

```{toctree}
:maxdepth: 2
console-output
testing
typing
```

(integration)=

## Integration with Existing Systems

*structlog* is both zero-config as well as highly configurable.
You can use it on its own or integrate with existing systems.
Dedicated support for the standard library and Twisted is shipped out-of-the-box.

```{toctree}
:maxdepth: 2

standard-library
twisted
```


## *structlog* in Practice

The following chapters deal with consideration of using *structlog* in the real world.


```{toctree}
:maxdepth: 2

recipes
logging-best-practices
performance
```


## Deprecated Features

```{toctree}
:maxdepth: 1

thread-local
```


## API Reference

```{toctree}
:maxdepth: 2

api
```


## Project Information

```{eval-rst}
.. include:: ../README.md
   :parser: myst_parser.sphinx_
   :start-after: ## Project Information

```

% stop Sphinx from complaints about orphaned docs, we link them elsewhere

```{toctree}
:hidden: true

license
changelog
```


## Indices and tables

- {any}`genindex`
- {any}`modindex`
