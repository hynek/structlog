# structlog

*Simple. Powerful. Fast. Pick three.*

Release **{sub-ref}`release`**  ([What's new?](changelog))

```{eval-rst}
.. include:: ../README.md
   :parser: myst_parser.sphinx_
   :start-after: <!-- begin-short -->
   :end-before: <!-- end-short -->

```


## First Steps

- If you're not sure whether *structlog* is for you, have a look at {doc}`why`.
- If you can't wait to log your first entry, start at {doc}`getting-started` and then work yourself through our tutorial.
- Once you have basic grasp of how *structlog* works, acquaint yourself with the [integrations](integration) *structlog* is shipping with.


## User's Guide

### Basics

```{toctree}
:maxdepth: 2

why
getting-started
bound-loggers
configuration
processors
contextvars
development
testing
typing
```

(integration)=

### Integration with Existing Systems

*structlog* is both zero-config as well as highly configurable.
You can use it on its own or integrate with existing systems.
Dedicated support for the standard library and Twisted is shipped out-of-the-box.

```{toctree}
:maxdepth: 2

frameworks
standard-library
twisted
```


### Advanced Topics

```{toctree}
:maxdepth: 2

logging-best-practices
performance
custom-wrappers
```


### Deprecated Features

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
