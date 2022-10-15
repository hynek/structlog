# structlog

<p align="center">
   <a href="https://www.structlog.org/">
      <img src="_static/structlog_logo_transparent.png" width="35%" alt="structlog" />
   </a>
</p>

<p align="center">
    <em>Simple. Powerful. Fast. Pick three.</em>
</p>

Release **{sub-ref}`release`**  ([What's new?](changelog))

---

```{eval-rst}
.. include:: ../README.md
   :parser: myst_parser.sphinx_
   :start-after: <!-- begin-short -->
   :end-before: <!-- end-short -->

```

## Basics

The following chapters give you all the concepts that you need to use *structlog* productively.
If you're already convinced that you want to play with it, skip ahead to our [Getting Started tutorial](getting-started.md)!
The remaining chapters build gently on each other.


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
