# structlog

*Simple. Powerful. Fast. Pick three.*

Release **{sub-ref}`release`**  ([What's new?](https://github.com/hynek/structlog/blob/main/CHANGELOG.md))

---

```{include} ../README.md
:start-after: <!-- begin-short -->
:end-before: <!-- end-short -->
```


If you’d like more information on why structured logging in general – and *structlog* in particular – are good ideas, we’ve prepared a [summary](why.md) just for you.

Otherwise, let’s dive right in!

```{toctree}
:hidden: true

why
```


## Basics

The first chapters teach you all you need to use *structlog* productively.
They build gently on each other, so ideally, read them in order.
If anything seems confusing, don't hesitate to have a look at our {doc}`glossary`!


```{toctree}
:maxdepth: 2

getting-started
bound-loggers
configuration
processors
contextvars
exceptions
```


## Development Affordances

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

frameworks
standard-library
twisted
```


## *structlog* in Practice

The following chapters deal with considerations of using *structlog* in the real world.


```{toctree}
:maxdepth: 2

recipes
logging-best-practices
performance
```


## Reference

```{toctree}
:maxdepth: 2

api
glossary
```


## Deprecated Features

```{toctree}
:maxdepth: 1

thread-local
```


## Indices and tables

- {any}`genindex`
- {any}`modindex`
- {any}`glossary`


```{toctree}
:hidden:
:caption: Meta

license
PyPI <https://pypi.org/project/structlog/>
GitHub <https://github.com/hynek/structlog/>
Changelog <https://github.com/hynek/structlog/blob/main/CHANGELOG.md>
Contributing <https://github.com/hynek/structlog/blob/main/.github/CONTRIBUTING.md>
Security Policy <https://github.com/hynek/structlog/blob/main/.github/SECURITY.md>
Funding <https://hynek.me/say-thanks/>
```
