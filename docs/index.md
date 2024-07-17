# structlog

*Simple. Powerful. Fast. Pick three.*

Release **{sub-ref}`release`**  ([What's new?](https://github.com/hynek/structlog/blob/main/CHANGELOG.md))

---

```{include} ../README.md
:start-after: <!-- begin-short -->
:end-before: <!-- pause-short -->
```

<!-- [[[cog
import pathlib, tomllib, importlib.metadata

if "dev" in (version := importlib.metadata.version("structlog")):
    version = "latest"

for sponsor in tomllib.loads(pathlib.Path("pyproject.toml").read_text())["tool"]["sponcon"]["sponsors"]:
      print(f'<a href="{sponsor["url"]}"><img title="{sponsor["title"]}" src="/en/{version}/_static/sponsors/{sponsor["img"]}" width="200" height="60" /></a>')
]]] -->
<a href="https://www.variomedia.de/"><img title="Variomedia AG" src="/en/latest/_static/sponsors/Variomedia.svg" width="200" height="60" /></a>
<a href="https://tidelift.com/?utm_source=lifter&utm_medium=referral&utm_campaign=hynek"><img title="Tidelift" src="/en/latest/_static/sponsors/Tidelift.svg" width="200" height="60" /></a>
<a href="https://klaviyo.com/"><img title="Klaviyo" src="/en/latest/_static/sponsors/Klaviyo.svg" width="200" height="60" /></a>
<a href="https://filepreviews.io/"><img title="FilePreviews" src="/en/latest/_static/sponsors/FilePreviews.svg" width="200" height="60" /></a>
<!-- [[[end]]] -->

```{include} ../README.md
:start-after: <!-- continue-short -->
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
:caption: Basics

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
:caption: Development Affordances

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
:caption: Integrations

frameworks
standard-library
twisted
```


## *structlog* in Practice

The following chapters deal with considerations of using *structlog* in the real world.


```{toctree}
:maxdepth: 2
:caption: In Practice

recipes
logging-best-practices
performance
```


## Reference

```{toctree}
:maxdepth: 2
:caption: Reference

api
glossary
genindex
modindex
```


## Deprecated Features

```{toctree}
:maxdepth: 1
:caption: Deprecated Features

thread-local
```


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
