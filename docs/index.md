# structlog

*Simple. Powerful. Fast. Pick three.*

Release **{sub-ref}`release`**  ([What's new?](https://github.com/hynek/structlog/blob/main/CHANGELOG.md))

---

```{include} ../README.md
:start-after: <!-- begin-short -->
:end-before: <!-- pause-short -->
```

<!-- [[[cog
# This is mainly called from RTD's pre_build job!

import pathlib, tomllib

for sponsor in tomllib.loads(pathlib.Path("pyproject.toml").read_text())["tool"]["sponcon"]["sponsors"]:
      print(f'<a href="{sponsor["url"]}"><img title="{sponsor["title"]}" src="_static/sponsors/{sponsor["img"]}" width="190" /></a>')
]]] -->
<a href="https://www.variomedia.de/"><img title="Variomedia AG" src="_static/sponsors/Variomedia.svg" width="190" /></a>
<a href="https://tidelift.com/?utm_source=lifter&utm_medium=referral&utm_campaign=hynek"><img title="Tidelift" src="_static/sponsors/Tidelift.svg" width="190" /></a>
<a href="https://kraken.tech/"><img title="Kraken Tech" src="_static/sponsors/Kraken.svg" width="190" /></a>
<a href="https://privacy-solutions.org/"><img title="Privacy Solutions" src="_static/sponsors/Privacy-Solutions.svg" width="190" /></a>
<a href="https://filepreviews.io/"><img title="FilePreviews" src="_static/sponsors/FilePreviews.svg" width="190" /></a>
<a href="https://www.testmu.ai/?utm_source=structlog&utm_medium=sponsor"><img title="TestMu AI" src="_static/sponsors/TestMu-AI.svg" width="190" /></a>
<a href="https://polar.sh/"><img title="Polar" src="_static/sponsors/Polar.svg" width="190" /></a>
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


## Development affordances

*structlog*'s focus is on production systems, but it comes with **pretty console logging** and handy in-development helpers both for your **comfort** and your code's **quality**.

```{toctree}
:maxdepth: 2
:caption: Development Affordances

console-output
testing
typing
```

(integration)=

## Integration with existing systems

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


## *structlog* in practice

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


## Deprecated features

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
