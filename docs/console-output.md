# Console Output

To make development a more pleasurable experience, *structlog* comes with the {mod}`structlog.dev` module.

The highlight is {class}`structlog.dev.ConsoleRenderer` that offers nicely aligned and colorful[^win] console output.

[^win]: Requires the [*Colorama* package](https://pypi.org/project/colorama/) on Windows.

If either of the [*Rich*](https://rich.readthedocs.io/) or [*better-exceptions*](https://github.com/Qix-/better-exceptions) packages is installed, it will also pretty-print exceptions with helpful contextual data.
*Rich* takes precedence over *better-exceptions*, but you can configure it by passing {func}`structlog.dev.plain_traceback` or {func}`structlog.dev.better_traceback` for the `exception_formatter` parameter of {class}`~structlog.dev.ConsoleRenderer`.

The following output is rendered using *Rich*:

```{figure} _static/console_renderer.png
Colorful console output by ConsoleRenderer.
```

You can find the code for the output above [in the repo](https://github.com/hynek/structlog/blob/main/show_off.py).

To use it, just add it as a renderer to your processor chain.
It will recognize logger names, log levels, time stamps, stack infos, and `exc_info` as produced by *structlog*'s processors and render them in special ways.

:::{warning}
For pretty exceptions to work, {func}`~structlog.processors.format_exc_info` must be **absent** from the processors chain.
:::

*structlog*'s default configuration already uses {class}`~structlog.dev.ConsoleRenderer`, therefore if you want nice colorful output on the console, you don't have to do anything except installing *Rich* or *better-exceptions* (and *Colorama* on Windows).
If you want to use it along with standard library logging, we suggest the following configuration:

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S"),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer()  # <===
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```


## Standard Environment Variables

*structlog*'s default configuration uses colors if standard out is a TTY (i.e. an interactive session).

It's possible to override this behavior by setting two standard environment variables to any value except an empty string:

- `FORCE_COLOR` *activates* colors, regardless of where output is going.
- [`NO_COLOR`](https://no-color.org) *disables* colors, regardless of where the output is going and regardless the value of `FORCE_COLOR`.
  Please note that `NO_COLOR` disables _all_ styling, including bold and italics.


## Disabling Exception Pretty-Printing

If you prefer the default terse Exception rendering, but still want *Rich* installed, you can disable the pretty-printing by instantiating {class}`structlog.dev.ConsoleRenderer()` yourself and passing `exception_formatter=structlog.dev.plain_traceback`.
