# structlog

*Simple. Powerful. Fast. Pick three.*

Release **{sub-ref}`release`**  ([What's new?](changelog))

```{eval-rst}
.. include:: ../README.md
   :parser: myst_parser.sphinx_
   :start-after: <!-- begin-short -->
   :end-before: <!-- end-short -->

```

## Basics

The following chapters give you the all the concepts that you need to use *structlog* productively.
If you're already convinced that you want to play with it, start with our [Getting Started tutorial](getting-started.md)!
The rest of the chapters builds gently on each other.


```{toctree}
:maxdepth: 2

why
getting-started
bound-loggers
configuration
processors
contextvars
```


## In-Development Affordances

*structlog*'s focus are production systems, but it comes with **pretty console logging** and handy in-development helpers for **comfort** and **better results**.

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

```{toctree}
:maxdepth: 2

recipes
logging-best-practices
performance
custom-wrappers
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
