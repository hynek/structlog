# structlog: Structured Logging for Python

<p align="center">
   <a href="https://www.structlog.org/">
      <img src="docs/_static/structlog_logo_transparent.png" width="35%" alt="structlog" />
   </a>
</p>

<p align="center">
   <a href="https://www.structlog.org/en/stable/?badge=stable">
       <img src="https://img.shields.io/badge/Docs-Read%20The%20Docs-black" alt="Documentation" />
   </a>
   <a href="https://github.com/hynek/structlog/blob/main/LICENSE">
      <img src="https://img.shields.io/badge/license-MIT%2FApache--2.0-C06524" alt="License: MIT / Apache 2.0" />
   </a>
   <a href="https://pypi.org/project/structlog/">
      <img src="https://img.shields.io/pypi/v/structlog" alt="PyPI release" />
   </a>
   <a href="https://pepy.tech/project/structlog">
      <img src="https://static.pepy.tech/personalized-badge/structlog?period=month&units=international_system&left_color=grey&right_color=blue&left_text=Downloads%20/%20Month" alt="Downloads per month" />
   </a>
</p>

<!-- begin-short -->

`structlog` makes logging in Python **faster**, **less painful**, and **more powerful** by adding **structure** to your log entries. It has been successfully used in production at every scale since **2013**, while embracing cutting-edge technologies like *asyncio* or type hints along the way, and [influenced the design](https://twitter.com/sirupsen/status/638330548361019392) of [structured logging packages in other ecosystems](https://github.com/sirupsen/logrus).

Thanks to its highly flexible design, it's up to you whether you want `structlog` to take care about the **output** of your log entries or whether you prefer to **forward** them to an existing logging system like the standard library's `logging` module.

`structlog` comes with support for JSON, [*logfmt*](https://brandur.org/logfmt), as well as pretty console output out-of-the-box:

![image](https://github.com/hynek/structlog/blob/main/docs/_static/console_renderer.png?raw=true)

<!-- end-short -->

A short explanation on *why* structured logging is good for you, and why `structlog` is the right tool for the job can be found in the [Why chapter](https://www.structlog.org/en/stable/why.html) of our documentation.

Once you feel inspired to try it out, check out our friendly [Getting Started tutorial](https://www.structlog.org/en/stable/getting-started.html) that also contains detailed installation instructions!

If you prefer videos over reading, check out [Markus Holtermann](https://twitter.com/m_holtermann)'s DjangoCon Europe 2019 talk: [*Logging Rethought 2: The Actions of Frank Taylor Jr.*](https://www.youtube.com/watch?v=Y5eyEgyHLLo)


<!-- begin-meta -->

## Project Information

- **License**: *dual* [Apache License, version 2 and MIT](https://www.structlog.org/en/stable/license.html)
- **PyPI**: <https://pypi.org/project/structlog/>
- **Source Code**: <https://github.com/hynek/structlog>
- **Documentation**: <https://www.structlog.org/>
- **Changelog**: <https://www.structlog.org/en/stable/changelog.html>
- **Get Help**: please use the `structlog` tag on [StackOverflow](https://stackoverflow.com/questions/tagged/structlog)
- **Third-party Extensions**: <https://github.com/hynek/structlog/wiki/Third-party-Extensions>
- **Supported Python Versions**: 3.7 and later


## `structlog` for Enterprise

Available as part of the Tidelift Subscription.

The maintainers of structlog and thousands of other packages are working with Tidelift to deliver commercial support and maintenance for the open source packages you use to build your applications. Save time, reduce risk, and improve code health, while paying the maintainers of the exact packages you use. [Learn more.](https://tidelift.com/subscription/pkg/pypi-structlog?utm_source=pypi-structlog&utm_medium=referral&utm_campaign=readme)
