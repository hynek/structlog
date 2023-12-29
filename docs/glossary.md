# Glossary

Please feel free to [file an issue](https://github.com/hynek/structlog/issues) if you think some important concept is missing here.

:::{glossary}

Event Dictionary
    Often abbreviated as *event dict*.
    It's a dictionary that contains all the information that is logged, with the `event` key having the special role of being the name of the event.

    It's the result of the values bound to the {term}`bound logger`'s context and the key-value pairs passed to the logging method.
    It is then passed through the {term}`processor` chain that can add, modify, and even remove key-value pairs.

Bound Logger
    An instance of a {class}`structlog.typing.BindableLogger` that is returned by either {func}`structlog.get_logger` or the bind/unbind/new methods on it.

    As the name suggests, it's possible to bind key-value pairs to it -- this data is called the {term}`context` of the logger.

    Its methods are the user's logging API and depend on the type of the bound logger.
    The two most common implementations are {class}`structlog.BoundLogger` and {class}`structlog.stdlib.BoundLogger`.

    Bound loggers are **immutable**.
    The context can only be modified by creating a new bound logger using its `bind()`and `unbind()` methods.

    :::{seealso}
    {doc}`bound-loggers`
    :::

Context
    A dictionary of key-value pairs belonging to a {term}`bound logger`.
    When a log entry is logged out, the context is the base for the event dictionary with the keyword arguments of the logging method call merged in.

    Bound loggers are **immutable**, so it's not possible to modify a context directly.
    But you can create a new bound logger with a different context using its `bind()` and `unbind()` methods.

Native Loggers
    Loggers created using {func}`structlog.make_filtering_bound_logger` which includes the default configuration.

    These loggers are very fast and do **not** use the standard library.

Wrapped Logger
    The logger that is wrapped by *structlog* and that is responsible for the actual output.

    By default it's a {class}`structlog.PrintLogger` for native logging.
    Another popular choice is {class}`logging.Logger` for standard library logging.

    :::{seealso}
    {doc}`standard-library`
    :::

Processor
    A callable that is called on every log entry.

    It receives the return value of its predecessor as an argument and returns a new event dictionary.
    This allows for composable transformations of the event dictionary.

    The result of the final processor is passed to the {term}`wrapped logger`.

    :::{seealso}
    {doc}`processors`
    :::

:::
