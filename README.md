# *structlog*: Structured Logging for Python

<p align="center">
   <a href="https://www.structlog.org/">
      <img src="docs/_static/structlog_logo.svg" width="35%" alt="structlog: Structured Logging for Python" />
   </a>
</p>

<p align="center">
   <a href="https://www.structlog.org/en/stable/?badge=stable"><img src="https://img.shields.io/badge/Docs-Read%20The%20Docs-black" alt="Documentation" /></a>
   <a href="https://github.com/hynek/structlog/blob/main/COPYRIGHT"><img src="https://img.shields.io/badge/license-MIT%2FApache--2.0-C06524" alt="License: MIT / Apache 2.0" /></a>
   <a href="https://bestpractices.coreinfrastructure.org/projects/6560"><img src="https://bestpractices.coreinfrastructure.org/projects/6560/badge"></a>
   <a href="https://doi.org/10.5281/zenodo.7353739"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.7353739.svg" alt="DOI"></a>
   <a href="https://pypi.org/project/structlog/"><img src="https://img.shields.io/pypi/pyversions/structlog.svg" alt="Supported Python versions of the current PyPI release." /></a>
   <a href="https://pepy.tech/project/structlog"><img src="https://static.pepy.tech/personalized-badge/structlog?period=month&units=international_system&left_color=grey&right_color=blue&left_text=Downloads%20/%20Month" alt="Downloads per month" /></a>
</p>

<p align="center"><em>Simple. Powerful. Fast. Pick three.</em></p>

<!-- begin-short -->

*structlog* is *the* production-ready logging solution for Python:

- **Simple**: Everything is about **functions** that take and return **dictionaries** – all hidden behind **familiar APIs**.
- **Powerful**: Functions and dictionaries aren’t just simple but also powerful.
  *structlog* leaves *you* in control.
- **Fast**: *structlog* is not hamstrung by designs of yore.
  Its flexibility comes not at the price of performance.

Thanks to its flexible design, *you* choose whether you want *structlog* to take care of the **output** of your log entries or whether you prefer to **forward** them to an existing logging system like the standard library's `logging` module.

The output format is just as flexible and *structlog* comes with support for JSON, [*logfmt*](https://brandur.org/logfmt), as well as pretty console output out-of-the-box:

[![image](https://github.com/hynek/structlog/blob/main/docs/_static/console_renderer.png?raw=true)](https://github.com/hynek/structlog/blob/main/docs/_static/console_renderer.png?raw=true)


## Sponsors

*structlog* would not be possible without our [amazing sponsors](https://github.com/sponsors/hynek).
Especially those generously supporting us at the *The Organization* tier and higher:

<!-- pause-short -->

<p align="center">

<!-- [[[cog
import pathlib, tomllib

for sponsor in tomllib.loads(pathlib.Path("pyproject.toml").read_text())["tool"]["sponcon"]["sponsors"]:
      print(f'<a href="{sponsor["url"]}"><img title="{sponsor["title"]}" src="docs/_static/sponsors/{sponsor["img"]}" width="190" /></a>')
]]] -->
<a href="https://www.variomedia.de/"><img title="Variomedia AG" src="docs/_static/sponsors/Variomedia.svg" width="190" /></a>
<a href="https://tidelift.com/?utm_source=lifter&utm_medium=referral&utm_campaign=hynek"><img title="Tidelift" src="docs/_static/sponsors/Tidelift.svg" width="190" /></a>
<a href="https://klaviyo.com/"><img title="Klaviyo" src="docs/_static/sponsors/Klaviyo.svg" width="190" /></a>
<a href="https://www.emsys-renewables.com/"><img title="emsys renewables" src="docs/_static/sponsors/emsys-renewables.svg" width="190" /></a>
<a href="https://filepreviews.io/"><img title="FilePreviews" src="docs/_static/sponsors/FilePreviews.svg" width="190" /></a>
<a href="https://polar.sh/"><img title="Polar" src="docs/_static/sponsors/Polar.svg" width="190" /></a>
<!-- [[[end]]] -->

</p>

<!-- continue-short -->

<p align="center">
   <strong>Please consider <a href="https://github.com/sponsors/hynek">joining them</a> to help make <em>structlog</em>’s maintenance more sustainable!</strong>
</p>

## Introduction

*structlog* has been successfully used in production at every scale since **2013**, while embracing cutting-edge technologies like *asyncio*, context variables, or type hints as they emerged.
Its paradigms proved influential enough to [help design](https://twitter.com/sirupsen/status/638330548361019392) structured logging [packages across ecosystems](https://github.com/sirupsen/logrus).

<!-- end-short -->

A short explanation on *why* structured logging is good for you, and why *structlog* is the right tool for the job can be found in the [Why chapter](https://www.structlog.org/en/stable/why.html) of our documentation.

Once you feel inspired to try it out, check out our friendly [Getting Started tutorial](https://www.structlog.org/en/stable/getting-started.html).

<!-- begin tutorials -->
For a fully-fledged zero-to-hero tutorial, check out [*A Comprehensive Guide to Python Logging with structlog*](https://betterstack.com/community/guides/logging/structlog/).

If you prefer videos over reading, check out [Markus Holtermann](https://chaos.social/@markush)'s talk *Logging Rethought 2: The Actions of Frank Taylor Jr.*:

<p align="center">
   <a href="https://www.youtube.com/watch?v=Y5eyEgyHLLo">
      <img width="50%" src="https://img.youtube.com/vi/Y5eyEgyHLLo/maxresdefault.jpg">
   </a>
</p>
<!-- end tutorials -->

## Credits

*structlog* is written and maintained by [Hynek Schlawack](https://hynek.me/).
The idea of bound loggers is inspired by previous work by [Jean-Paul Calderone](https://github.com/exarkun) and [David Reid](https://github.com/dreid).

The development is kindly supported by my employer [Variomedia AG](https://www.variomedia.de/), *structlog*’s [Tidelift subscribers](https://tidelift.com/?utm_source=lifter&utm_medium=referral&utm_campaign=hynek), and all my amazing [GitHub Sponsors](https://github.com/sponsors/hynek).

The logs-loving beaver logo has been contributed by [Lynn Root](https://www.roguelynn.com).


<!-- begin-meta -->

## Project Links

- [**Get Help**](https://stackoverflow.com/questions/tagged/structlog) (use the *structlog* tag on Stack Overflow)
- [**PyPI**](https://pypi.org/project/structlog/)
- [**GitHub**](https://github.com/hynek/structlog)
- [**Documentation**](https://www.structlog.org/)
- [**Changelog**](https://github.com/hynek/structlog/tree/main/CHANGELOG.md)
- [**Third-party Extensions**](https://github.com/hynek/structlog/wiki/Third-party-Extensions)


## *structlog* for Enterprise

Available as part of the [Tidelift Subscription](https://tidelift.com/?utm_source=lifter&utm_medium=referral&utm_campaign=hynek).

The maintainers of *structlog* and thousands of other packages are working with Tidelift to deliver commercial support and maintenance for the open source packages you use to build your applications.
Save time, reduce risk, and improve code health, while paying the maintainers of the exact packages you use.
