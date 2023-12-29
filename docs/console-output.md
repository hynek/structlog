# Console Output

To make development a more pleasurable experience, *structlog* comes with the {mod}`structlog.dev` module.

The highlight is {class}`structlog.dev.ConsoleRenderer` that offers nicely aligned and colorful[^win] console output.

[^win]: Requires the [Colorama package](https://pypi.org/project/colorama/) on Windows.

If either of the [Rich](https://rich.readthedocs.io/) or [*better-exceptions*](https://github.com/Qix-/better-exceptions) packages is installed, it will also pretty-print exceptions with helpful contextual data.
Rich takes precedence over *better-exceptions*, but you can configure it by passing {func}`structlog.dev.plain_traceback` or {func}`structlog.dev.better_traceback` for the `exception_formatter` parameter of {class}`~structlog.dev.ConsoleRenderer`.

The following output is rendered using Rich:

```{figure} _static/console_renderer.png
Colorful console output by ConsoleRenderer.
```

You can find the code for the output above [in the repo](https://github.com/hynek/structlog/blob/main/show_off.py).

To use it, just add it as a renderer to your processor chain.
It will recognize logger names, log levels, time stamps, stack infos, and `exc_info` as produced by *structlog*'s processors and render them in special ways.

:::{warning}
For pretty exceptions to work, {func}`~structlog.processors.format_exc_info` must be **absent** from the processors chain.
:::

*structlog*'s default configuration already uses {class}`~structlog.dev.ConsoleRenderer`, therefore if you want nice colorful output on the console, you don't have to do anything except installing Rich or *better-exceptions* (and Colorama on Windows).
If you want to use it along with standard library logging, there's the {func}`structlog.stdlib.recreate_defaults` helper.

:::{seealso}
{doc}`exceptions` for more information on how to configure exception rendering.
For the console and beyond.
:::

(columns-config)=

## Console Output Configuration

:::{versionadded} 23.3.0
:::

You can freely configure how the key-value pairs are formatted: colors, order, and how values are stringified.

For that {class}`~structlog.dev.ConsoleRenderer` accepts the *columns* parameter that takes a list of {class}`~structlog.dev.Column`s.
It allows you to assign a formatter to each key and a default formatter for the rest (by passing an empty key name).
The order of the column definitions is the order in which the columns are rendered;
the rest is -- depending on the *sort_keys* argument to {class}`~structlog.dev.ConsoleRenderer` -- either sorted alphabetically or in the order of the keys in the event dictionary.

You can use a column definition to drop a key-value pair from the output by returning an empty string from the formatter.

When the API talks about "styles", it means ANSI control strings.
You can find them, for example, in [Colorama](https://github.com/tartley/colorama).


It's best demonstrated by an example:

```python
import structlog
import colorama

cr = structlog.dev.ConsoleRenderer(
    columns=[
        # Render the timestamp without the key name in yellow.
        structlog.dev.Column(
            "timestamp",
            structlog.dev.KeyValueColumnFormatter(
                key_style=None,
                value_style=colorama.Fore.YELLOW,
                reset_style=colorama.Style.RESET_ALL,
                value_repr=str,
            ),
        ),
        # Render the event without the key name in bright magenta.
        structlog.dev.Column(
            "event",
            structlog.dev.KeyValueColumnFormatter(
                key_style=None,
                value_style=colorama.Style.BRIGHT + colorama.Fore.MAGENTA,
                reset_style=colorama.Style.RESET_ALL,
                value_repr=str,
            ),
        ),
        # Default formatter for all keys not explicitly mentioned. The key is
        # cyan, the value is green.
        structlog.dev.Column(
            "",
            structlog.dev.KeyValueColumnFormatter(
                key_style=colorama.Fore.CYAN,
                value_style=colorama.Fore.GREEN,
                reset_style=colorama.Style.RESET_ALL,
                value_repr=str,
            ),
        ),
    ]
)

structlog.configure(processors=structlog.get_config()["processors"][:-1]+[cr])
```

:::{hint}
You can replace only the last processor using:

```python
structlog.configure(processors=structlog.get_config()["processors"][:-1]+[cr])
```
:::


## Standard Environment Variables

*structlog*'s default configuration uses colors if standard out is a TTY (that is, an interactive session).

It's possible to override this behavior by setting two standard environment variables to any value except an empty string:

- `FORCE_COLOR` *activates* colors, regardless of where output is going.
- [`NO_COLOR`](https://no-color.org) *disables* colors, regardless of where the output is going and regardless the value of `FORCE_COLOR`.
  Please note that `NO_COLOR` disables _all_ styling, including bold and italics.


## Disabling Exception Pretty-Printing

If you prefer the default terse Exception rendering, but still want Rich installed, you can disable the pretty-printing by instantiating {class}`structlog.dev.ConsoleRenderer()` yourself and passing `exception_formatter=structlog.dev.plain_traceback`.
