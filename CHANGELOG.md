# Changelog

All notable changes to this project will be documented in this file.

The format is based on [*Keep a Changelog*](https://keepachangelog.com/en/1.0.0/) and this project adheres to [*Calendar Versioning*](https://calver.org/).

The **first number** of the version is the year.
The **second number** is incremented with each release, starting at 1 for each year.
The **third number** is for emergencies when we need to start branches for older releases.

You shouldn't ever be afraid to upgrade `structlog` if you're using its public APIs and pay attention to `DeprecationWarning`s.
Whenever there is a need to break compatibility, it is announced here in the changelog and raises a `DeprecationWarning` for a year (if possible) before it's finally really broken.

You cannot rely on the default settings and the `structlog.dev` module.
They may be adjusted in the future to provide a better experience when starting to use `structlog`.
So please make sure to **always** properly configure your applications.

<!-- changelog follows -->

## [Unreleased](https://github.com/hynek/structlog/compare/22.1.0...HEAD)

### Deprecated

- Accessing package metadata as attributes on the `structlog` module is deprecated (e.g. `structlog.__version__`).
  Please use [`importlib.metadata`](https://docs.python.org/3.10/library/importlib.metadata.html) instead (for Python 3.7: the [*importlib-metadata*](https://pypi.org/project/importlib-metadata/) PyPI package).


### Added

- `FilteringBoundLogger` (used by default) now allows for string interpolation using positional arguments:

  ```pycon
  >>> log.info("Hello %s! The answer is %d.", "World", 42, x=1)
  2022-10-07 10:04.31 [info     ] Hello World! The answer is 42. x=1
  ```

  [#454](https://github.com/hynek/structlog/pull/454)


### Changed

- The build backend has been switched to [*Hatch*](https://hatch.pypa.io/).


### Fixed

- The timestamps in the default configuration now use the correct separator (`:`) for seconds.


## [22.1.0](https://github.com/hynek/structlog/compare/21.5.0...22.1.0) - 2022-07-20

### Removed

- Python 3.6 is not supported anymore.
- Pickling is now only possible with protocol version 3 and newer.


### Deprecated

- The entire `structlog.threadlocal` module is deprecated.
  Please use the primitives from `structlog.contextvars` instead.

  If you're using the modern APIs (`bind_threadlocal()` / `merge_threadlocal()`) it's enough to replace them 1:1 with their `contextvars` counterparts.
  The old approach around `wrap_dict()` has been discouraged for a while.

  Currently there are no concrete plans to remove the module, but no patches against it will be accepted from now on.
  [#409](https://github.com/hynek/structlog/pull/409)


### Added

- `structlog.processors.StackInfoRenderer` now has an *additional_ignores* parameter that allows you to filter out your own logging layer.
  [#396](https://github.com/hynek/structlog/issues/396)
- Added `structlog.WriteLogger`, a faster – but more low-level – alternative to `structlog.PrintLogger`.
  It works the way `PrintLogger` used to work in previous versions.
  [#403](https://github.com/hynek/structlog/pull/403)
  [#404](https://github.com/hynek/structlog/pull/404)
- `structlog.make_filtering_bound_logger()`-returned loggers now also have a `log()` method to match the `structlog.stdlib.BoundLogger` signature closer.
  [#413](https://github.com/hynek/structlog/pull/413)
- Added structured logging of tracebacks via the `structlog.tracebacks` module,
  and most notably the `structlog.tracebacks.ExceptionDictTransformer` which can be used with the new `structlog.processors.ExceptionRenderer` to render JSON tracebacks.
  [#407](https://github.com/hynek/structlog/pull/407)
- `structlog.stdlib.recreate_defaults(log_level=logging.NOTSET)` that recreates `structlog`'s defaults on top of standard library's `logging`.
  It optionally also configures `logging` to log to standard out at the passed log level.
  [#428](https://github.com/hynek/structlog/pull/428)
- `structlog.processors.EventRenamer` allows you to rename the hitherto hard-coded event dict key `event` to something else.
  Optionally, you can rename another key to `event` at the same time, too.
  So adding `EventRenamer(to="msg", replace_by="_event")` to your processor pipeline will rename the standard `event` key to `msg` and then rename the `_event` key to `event`.
  This allows you to use the `event` key in your own log files and to have consistent log message keys across languages.
- `structlog.dev.ConsoleRenderer(event_key="event")` now allows to customize the name of the key that is used for the log message.


### Changed

- `structlog.make_filtering_bound_logger()` now returns a method with the same signature for all log levels, whether they are active or not.
  This ensures that invalid calls to inactive log levels are caught immediately and don't explode once the log level changes.
  [#401](https://github.com/hynek/structlog/pull/401)
- `structlog.PrintLogger` – that is used by default – now uses `print()` for printing, making it a better citizen for interactive terminal applications.
  [#399](https://github.com/hynek/structlog/pull/399)
- `structlog.testing.capture_logs` now works for already initialized bound loggers.
  [#408](https://github.com/hynek/structlog/pull/412)
- `structlog.processors.format_exc_info()` is no longer a function, but an instance of `structlog.processors.ExceptionRenderer`.
  Its behavior has not changed.
  [#407](https://github.com/hynek/structlog/pull/407)
- The default configuration now includes the `structlog.contextvars.merge_contextvars` processor.
  That means you can use [`structlog.contextvars`](https://www.structlog.org/en/stable/contextvars.html) features without configuring `structlog`.


### Fixed

- Overloaded the `bind`, `unbind`, `try_unbind` and `new` methods in the `FilteringBoundLogger` [Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol).
  This makes it easier to use objects of type `FilteringBoundLogger` in a typed context.
  [#392](https://github.com/hynek/structlog/pull/392)
- Monkeypatched `sys.stdout`s are now handled more gracefully by `ConsoleRenderer` (that's used by default).
  [#404](https://github.com/hynek/structlog/pull/404)
- `structlog.stdlib.render_to_log_kwargs()` now correctly handles the presence of `exc_info`, `stack_info`, and `stackLevel` in the event dictionary.
  They are transformed into proper keyword arguments instead of putting them into the `extra` dictionary.
  [#424](https://github.com/hynek/structlog/issues/424),
  [#427](https://github.com/hynek/structlog/issues/427)


## [21.5.0](https://github.com/hynek/structlog/compare/21.4.0...21.5.0) - 2021-12-16

### Added

- Added the `structlog.processors.LogfmtRenderer` processor to render log lines using the [*logfmt*](https://brandur.org/logfmt) format.
  [#376](https://github.com/hynek/structlog/pull/376)
- Added the `structlog.stdlib.ExtraAdder` processor that adds extra attributes of `logging.LogRecord` objects to the event dictionary.
  This processor can be used for adding data passed in the `extra` parameter of the `logging` module's log methods to the event dictionary.
  [#209](https://github.com/hynek/structlog/pull/209),
  [#377](https://github.com/hynek/structlog/pull/377)
- Added the `structlog.processor.CallsiteParameterAdder` processor that adds parameters of the callsite that an event dictionary originated from to the event dictionary.
  This processor can be used to enrich events dictionaries with information such as the function name, line number and filename that an event dictionary originated from.
  [#380](https://github.com/hynek/structlog/pull/380)


## [21.4.0](https://github.com/hynek/structlog/compare/21.3.0...21.4.0) - 2021-11-25

### Added

- Added the `structlog.threadlocal.bound_threadlocal` and `structlog.contextvars.bound_contextvars` decorator/context managers to temporarily bind key/value pairs to a thread-local and context-local context.
  [#371](https://github.com/hynek/structlog/pull/371)


### Fixed

- Fixed import when running in optimized mode (`PYTHONOPTIMIZE=2` or `python -OO`)
.
  [#373](https://github.com/hynek/structlog/pull/373)


## [21.3.0](https://github.com/hynek/structlog/compare/21.2.0...21.3.0) - 2021-11-20

### Added

- `structlog.dev.ConsoleRenderer` now has `sort_keys` boolean parameter that allows to disable the sorting of keys on output.
  [#358](https://github.com/hynek/structlog/pull/358)


### Changed

- `structlog` switched its packaging to [*flit*](https://flit.pypa.io/).
  Users shouldn't notice a difference, but (re-)packagers might.
- `structlog.stdlib.AsyncBoundLogger` now determines the running loop when logging, not on instantiation.
  That has a minor performance impact, but makes it more robust when loops change (e.g. `aiohttp.web.run_app()`), or you want to use `sync_bl` *before* a loop has started.


### Fixed

- `structlog.processors.TimeStamper` now works well with [*FreezeGun*](https://github.com/spulec/freezegun) even when it gets applied before the loggers are configured.
  [#364](https://github.com/hynek/structlog/pull/364)

- `structlog.stdlib.ProcessorFormatter` now has a *processors* argument that allows to define a processor chain to run over *all* log entries.

  Before running the chain, two additional keys are added to the event dictionary: `_record` and `_from_structlog`.
  With them it's possible to extract information from `logging.LogRecord`s and differentiate between `structlog` and `logging` log entries while processing them.

  The old *processor* (singular) parameter is now deprecated, but no plans exist to remove it.
  [#365](https://github.com/hynek/structlog/pull/365)


## [21.2.0](https://github.com/hynek/structlog/compare/21.1.0...21.2.0) - 2021-10-12

### Added

- `structlog.threadlocal.get_threadlocal()` and `structlog.contextvars.get_contextvars()` can now be used to get a copy of the current thread-local/context-local context that has been bound using `structlog.threadlocal.bind_threadlocal()` and `structlog.contextvars.bind_contextvars()`.
  [#331](https://github.com/hynek/structlog/pull/331),
  [#337](https://github.com/hynek/structlog/pull/337)
- `structlog.threadlocal.get_merged_threadlocal(bl)` and `structlog.contextvars.get_merged_contextvars(bl)` do the same, but also merge the context from a bound logger *bl*.
  Same pull requests as previous change.
- `structlog.contextvars.bind_contextvars()` now returns a mapping of keys to `contextvars.Token`s, allowing you to reset values using the new `structlog.contextvars.reset_contextvars()`.
  [#339](https://github.com/hynek/structlog/pull/339)
- Exception rendering in `structlog.dev.ConsoleLogger` is now configurable using the `exception_formatter` setting.
  If either the [*Rich*](https://github.com/Textualize/rich) or the [*better-exceptions*](https://github.com/qix-/better-exceptions) package is present, `structlog` will use them for pretty-printing tracebacks.
  *Rich* takes precedence over *better-exceptions* if both are present.

  This only works if `format_exc_info` is **absent** in the processor chain.
  [#330](https://github.com/hynek/structlog/pull/330),
  [#349](https://github.com/hynek/structlog/pull/349)
- The final processor can now return a `bytearray` (additionally to `str` and `bytes`).
  [#344](https://github.com/hynek/structlog/issues/344)


### Changed

- To implement pretty exceptions (see Changes below), `structlog.dev.ConsoleRenderer` now formats exceptions itself.

  Make sure to remove `format_exc_info` from your processor chain if you configure `structlog` manually.
  This change is not really breaking, because the old use-case will keep working as before.
  However if you pass `pretty_exceptions=True` (which is the default if either `rich` or `better-exceptions` is installed), a warning will be raised and the exception will be rendered without prettification.
- All use of [*colorama*](https://github.com/tartley/colorama) on non-Windows systems has been excised.
  Thus, colors are now enabled by default in `structlog.dev.ConsoleRenderer` on non-Windows systems.
  You can keep using *colorama* to customize colors, of course.
  [#345](https://github.com/hynek/structlog/pull/345)


### Fixed

- `structlog` is now importable if `sys.stdout` is `None` (e.g. when running using `pythonw`). [#313](https://github.com/hynek/structlog/issues/313)


## [21.1.0](https://github.com/hynek/structlog/compare/20.2.0...21.1.0) - 2021-02-18

### Changed

- `structlog.dev.ConsoleRenderer` will now look for a `logger_name` key if no `logger` key is set.
  [#295](https://github.com/hynek/structlog/pull/295)


### Fixed

- `structlog.threadlocal.wrap_dict()` now has a correct type annotation.
  [#290](https://github.com/hynek/structlog/pull/290)
- Fix isolation in `structlog.contextvars`.
  [#302](https://github.com/hynek/structlog/pull/302)
- The default configuration and loggers are pickleable again.
  [#301](https://github.com/hynek/structlog/pull/301)


## [20.2.0](https://github.com/hynek/structlog/compare/20.1.0...20.2.0) - 2020-12-31

### Removed

- Python 2.7 and 3.5 aren't supported anymore.
  The package meta data should ensure that you keep getting 20.1.0 on those versions.
  [#244](https://github.com/hynek/structlog/pull/244)


### Deprecated

- Accessing the `_context` attribute of a bound logger is now deprecated.
  Please use the new `structlog.get_context()`.


### Added

- `structlog` has now type hints for all of its APIs!
  Since `structlog` is highly dynamic and configurable, this led to a few concessions like a specialized `structlog.stdlib.get_logger()` whose only difference to `structlog.get_logger()` is that it has the correct type hints.

  We consider them provisional for the time being – i.e. the backwards-compatibility does not apply to them in its full strength until we feel we got it right.
  Please feel free to provide feedback!
  [#223](https://github.com/hynek/structlog/issues/223),
  [#282](https://github.com/hynek/structlog/issues/282)
- Added `structlog.make_filtering_logger` that can be used like `configure(wrapper_class=make_filtering_bound_logger(logging.INFO))`.
  It creates a highly optimized bound logger whose inactive methods only consist of a `return None`.
  This is now also the default logger.
- As a complement, `structlog.stdlib.add_log_level()` can now additionally be imported as `structlog.processors.add_log_level` since it just adds the method name to the event dict.
- Added `structlog.BytesLogger` to avoid unnecessary encoding round trips.
  Concretely this is useful with *orjson* which returns bytes.
  [#271](https://github.com/hynek/structlog/issues/271)
- The final processor now also may return bytes that are passed untouched to the wrapped logger.
- `structlog.get_context()` allows you to retrieve the original context of a bound logger. [#266](https://github.com/hynek/structlog/issues/266),
- Added `structlog.testing.CapturingLogger` for more unit testing goodness.
- Added `structlog.stdlib.AsyncBoundLogger` that executes logging calls in a thread executor and therefore doesn't block.
  [#245](https://github.com/hynek/structlog/pull/245)


### Changed

- The default bound logger (`wrapper_class`) if you don't configure `structlog` has changed.
  It's mostly compatible with the old one but a few uncommon methods like `log`, `failure`, or `err` don't exist anymore.

  You can regain the old behavior by using `structlog.configure(wrapper_class=structlog.BoundLogger)`.

  Please note that due to the various interactions between settings, it's possible that you encounter even more errors.
  We **strongly** urge you to always configure all possible settings since the default configuration is *not* covered by our backwards-compatibility policy.
- `structlog.processors.add_log_level()` is now part of the default configuration.
- `structlog.stdlib.ProcessorFormatter` no longer uses exceptions for control flow, allowing `foreign_pre_chain` processors to use `sys.exc_info()` to access the real exception.


### Fixed

- `structlog.PrintLogger` now supports `copy.deepcopy()`.
  [#268](https://github.com/hynek/structlog/issues/268)


## [20.1.0](https://github.com/hynek/structlog/compare/19.2.0...20.1.0) - 2020-01-28

### Deprecated

- This is the last version to support Python 2.7 (including PyPy) and 3.5.
  All following versions will only support Python 3.6 or later.


### Added

- Added a new module `structlog.contextvars` that allows to have a global but context-local `structlog` context the same way as with `structlog.threadlocal` since 19.2.0.
  [#201](https://github.com/hynek/structlog/issues/201),
  [#236](https://github.com/hynek/structlog/pull/236)
- Added a new module `structlog.testing` for first class testing support.
  The first entry is the context manager `capture_logs()` that allows to make assertions about structured log calls.
  [#14](https://github.com/hynek/structlog/issues/14),
  [#234](https://github.com/hynek/structlog/pull/234)
- Added `structlog.threadlocal.unbind_threadlocal()`.
  [#239](https://github.com/hynek/structlog/pull/239)


### Fixed

- The logger created by `structlog.get_logger()` is not detected as an abstract method anymore, when attached to an abstract base class.
  [#229](https://github.com/hynek/structlog/issues/229)
- *colorama* isn't initialized lazily on Windows anymore because it breaks rendering.
  [#232](https://github.com/hynek/structlog/issues/232),
  [#242](https://github.com/hynek/structlog/pull/242)


## [19.2.0](https://github.com/hynek/structlog/compare/19.1.0...19.2.0) - 2019-10-16

### Removed

- Python 3.4 is not supported anymore.
It has been unsupported by the Python core team for a while now and its PyPI downloads are negligible.

  It's very unlikely that `structlog` will break under 3.4 anytime soon, but we don't test it anymore.


### Added

- Full Python 3.8 support for `structlog.stdlib`.
- Added more pass-through properties to `structlog.stdlib.BoundLogger`. To makes it easier to use it as a drop-in replacement for `logging.Logger`.
  [#198](https://github.com/hynek/structlog/issues/198)
- Added new processor `structlog.dev.set_exc_info()` that will set `exc_info=True` if the method's name is `exception` and `exc_info` isn't set at all.
  *This is only necessary when the standard library integration is not used*.
  It fixes the problem that in the default configuration, `structlog.get_logger().exception("hi")` in an `except` block would not print the exception without passing `exc_info=True` to it explicitly.
  [#130](https://github.com/hynek/structlog/issues/130),
  [#173](https://github.com/hynek/structlog/issues/173),
  [#200](https://github.com/hynek/structlog/issues/200),
  [#204](https://github.com/hynek/structlog/issues/204)
- Added a new thread-local API that allows binding values to a thread-local context explicitly without affecting the default behavior of `bind()`.
  [#222](https://github.com/hynek/structlog/issues/222),
  [#225](https://github.com/hynek/structlog/issues/225)
- Added *pass_foreign_args* argument to `structlog.stdlib.ProcessorFormatter`. It allows to pass a foreign log record's *args* attribute to the event dictionary under the `positional_args` key.
  [#228](https://github.com/hynek/structlog/issues/228)



### Changed

- `structlog.stdlib.ProcessorFormatter` now takes a logger object as an optional keyword argument.
  This makes `ProcessorFormatter` work properly with `stuctlog.stdlib.filter_by_level()`.
  [#219](https://github.com/hynek/structlog/issues/219)
- `structlog.dev.ConsoleRenderer` now calls `str()` on the event value. [#221](https://github.com/hynek/structlog/issues/221)


### Fixed

- `structlog.dev.ConsoleRenderer` now uses no colors by default, if *colorama* is not available.
  [#215](https://github.com/hynek/structlog/issues/215)
- `structlog.dev.ConsoleRenderer` now initializes *colorama* lazily, to prevent accidental side-effects just by importing `structlog`.
  [#210](https://github.com/hynek/structlog/issues/210)
- A best effort has been made to make as much of `structlog` pickleable as possible to make it friendlier with `multiprocessing` and similar libraries.
  Some classes can only be pickled on Python 3 or using the [dill](https://pypi.org/project/dill/) library though and that is very unlikely to change.

  So far, the configuration proxy, `structlog.processor.TimeStamper`, `structlog.BoundLogger`, `structlog.PrintLogger` and `structlog.dev.ConsoleRenderer` have been made pickleable.
  Please report if you need any another class fixed.
  [#126](https://github.com/hynek/structlog/issues/126)


## [19.1.0](https://github.com/hynek/structlog/compare/18.2.0...19.1.0) - 2019-02-02

### Added

- `structlog.ReturnLogger` and `structlog.PrintLogger` now have a `fatal()` log method.
  [#181](https://github.com/hynek/structlog/issues/181)


### Changed

- As announced in 18.1.0, `pip install -e .[dev]` now installs all development dependencies.
  Sorry for the inconveniences this undoubtedly will cause!
- `structlog` now tolerates passing through `dict`s to stdlib logging.
  [#187](https://github.com/hynek/structlog/issues/187),
  [#188](https://github.com/hynek/structlog/pull/188),
  [#189](https://github.com/hynek/structlog/pull/189)


### Fixed

- Under certain (rather unclear) circumstances, the frame extraction could throw an `SystemError: error return without exception set`.
  A workaround has been added.
  [#174](https://github.com/hynek/structlog/issues/174)


## [18.2.0](https://github.com/hynek/structlog/compare/18.1.0...18.2.0) - 2018-09-05

### Added

- Added `structlog.stdlib.add_log_level_number()` processor that adds the level *number* to the event dictionary.
  Can be used to simplify log filtering.
  [#151](https://github.com/hynek/structlog/pull/151)
- `structlog.processors.JSONRenderer` now allows for overwriting the *default* argument of its serializer.
  [#77](https://github.com/hynek/structlog/pull/77),
  [#163](https://github.com/hynek/structlog/pull/163)
- Added `try_unbind()` that works like `unbind()` but doesn't raise a `KeyError` if one of the keys is missing.
  [#171](https://github.com/hynek/structlog/pull/171)


## [18.1.0](https://github.com/hynek/structlog/compare/17.2.0...18.1.0) - 2018-01-27

### Deprecated

- The meaning of the `structlog[dev]` installation target will change from "colorful output" to "dependencies to develop `structlog`" in 19.1.0.

  The main reason behind this decision is that it's impossible to have a `structlog` in your normal dependencies and additionally a `structlog[dev]` for development (`pip` will report an error).


### Added

- `structlog.dev.ConsoleRenderer` now accepts a *force_colors* argument to output colored logs even if the destination is not a tty.
  Use this option if your logs are stored in files that are intended to be streamed to the console.
- `structlog.dev.ConsoleRenderer` now accepts a *level_styles* argument for overriding the colors for individual levels, as well as to add new levels.
  See the docs for `ConsoleRenderer.get_default_level_styles()` for usage.
  [#139](https://github.com/hynek/structlog/pull/139)
- Added `structlog.is_configured()` to check whether or not `structlog` has been configured.
- Added `structlog.get_config()` to introspect current configuration.


### Changed

- Empty strings are valid events now.
  [#110](https://github.com/hynek/structlog/issues/110)
- `structlog.stdlib.BoundLogger.exception()` now uses the `exc_info` argument if it has been passed instead of setting it unconditionally to `True`. [#149](https://github.com/hynek/structlog/pull/149)
- Default configuration now uses plain `dict`s on Python 3.6+ and PyPy since they are ordered by default.


### Fixed
- Do not encapsulate Twisted failures twice with newer versions of Twisted.
  [#144](https://github.com/hynek/structlog/issues/144)


## [17.2.0](https://github.com/hynek/structlog/compare/17.1.0...17.2.0) - 2017-05-15

### Added

- `structlog.stdlib.ProcessorFormatter` now accepts *keep_exc_info* and *keep_stack_info* arguments to control what to do with this information on log records.
  Most likely you want them both to be `False` therefore it's the default.
  [#109](https://github.com/hynek/structlog/issues/109)


### Fixed
- `structlog.stdlib.add_logger_name()` now works in `structlog.stdlib.ProcessorFormatter`'s `foreign_pre_chain`.
  [#112](https://github.com/hynek/structlog/issues/112)
- Clear log record args in `structlog.stdlib.ProcessorFormatter` after rendering.
  This fix is for you if you tried to use it and got `TypeError: not all arguments converted during string formatting` exceptions.
  [#116](https://github.com/hynek/structlog/issues/116),
  [#117](https://github.com/hynek/structlog/issues/117)


## [17.1.0](https://github.com/hynek/structlog/compare/16.1.0...17.1.0) - 2017-04-24

The main features of this release are massive improvements in standard library's `logging` integration.
Have a look at the updated [standard library chapter](https://www.structlog.org/en/stable/standard-library.html) on how to use them!
Special thanks go to [Fabian Büchler](https://github.com/fabianbuechler), [Gilbert Gilb's](https://github.com/gilbsgilbs), [Iva Kaneva](https://github.com/if-fi), [insolite](https://github.com/insolite), and [sky-code](https://github.com/sky-code), that made them possible.


### Added

- Added `structlog.stdlib.render_to_log_kwargs()`.
  This allows you to use `logging`-based formatters to take care of rendering your entries.
  [#98](https://github.com/hynek/structlog/issues/98)
- Added `structlog.stdlib.ProcessorFormatter` which does the opposite: This allows you to run `structlog` processors on arbitrary `logging.LogRecords`.
  [#79](https://github.com/hynek/structlog/issues/79),
  [#105](https://github.com/hynek/structlog/issues/105)
- Added *repr_native_str* to `structlog.processors.KeyValueRenderer` and `structlog.dev.ConsoleRenderer`.
  This allows for human-readable non-ASCII output on Python 2 (`repr()` on Python 2 behaves like `ascii()` on Python 3 in that regard).
  As per compatibility policy, it's on (original behavior) in `KeyValueRenderer` and off (human-friendly behavior) in `ConsoleRenderer`.
  [#94](https://github.com/hynek/structlog/issues/94)
- Added *colors* argument to `structlog.dev.ConsoleRenderer` and made it the default renderer.
  [#78](https://github.com/hynek/structlog/pull/78)


### Changed

- The default renderer now is `structlog.dev.ConsoleRenderer` if you don't configure `structlog`.
  Colors are used if available and human-friendly timestamps are prepended.
  This is in line with our backwards-compatibility policy that explicitly excludes default settings.
- UNIX epoch timestamps from `structlog.processors.TimeStamper` are more precise now.
- Positional arguments are now removed even if they are empty.
  [#82](https://github.com/hynek/structlog/pull/82)


## Fixed

- Fixed bug with Python 3 and `structlog.stdlib.BoundLogger.log()`.
  Error log level was not reproducible and was logged as exception one time out of two.
  [#92](https://github.com/hynek/structlog/pull/92)


## [16.1.0](https://github.com/hynek/structlog/compare/16.0.0...16.1.0) - 2016-05-24

### Removed

- Python 3.3 and 2.6 aren't supported anymore.
  They may work by chance but any effort to keep them working has ceased.

  The last Python 2.6 release was on October 29, 2013 and isn't supported by the CPython core team anymore.
  Major Python packages like Django and Twisted dropped Python 2.6 a while ago already.

  Python 3.3 never had a significant user base and wasn't part of any distribution's LTS release.


### Added

- Added a `drop_missing` argument to `KeyValueRenderer`.
  If `key_order` is used and a key is missing a value, it's not rendered at all instead of being rendered as `None`.
  [#67](https://github.com/hynek/structlog/pull/67)


### Fixed

- Exceptions without a `__traceback__` are now also rendered on Python 3.
- Don't cache loggers in lazy proxies returned from `get_logger()`.
  This lead to in-place mutation of them if used before configuration which in turn lead to the problem that configuration was applied only partially to them later.
  [#72](https://github.com/hynek/structlog/pull/72)


## [16.0.0](https://github.com/hynek/structlog/compare/15.3.0...16.0.0) - 2016-01-28

### Added

- Added `structlog.dev.ConsoleRenderer` that renders the event dictionary aligned and with colors.
- Added `structlog.processors.UnicodeDecoder` that will decode all byte string values in an event dictionary to Unicode.
- Added `serializer` parameter to `structlog.processors.JSONRenderer` which allows for using different (possibly faster) JSON encoders than the standard library.


### Changed

- `structlog.processors.ExceptionPrettyPrinter` and `structlog.processors.format_exc_info` now support passing of Exceptions on Python 3.
- [*six*](https://six.readthedocs.io/) is now used for compatibility.


### Fixed

- The context is now cleaned up when exiting `structlog.threadlocal.tmp_bind` in case of exceptions.
  [#64](https://github.com/hynek/structlog/issues/64)
- Be more more lenient about missing `__name__`s.
  [#62](https://github.com/hynek/structlog/pull/62)


## [15.3.0](https://github.com/hynek/structlog/compare/15.2.0...15.3.0) - 2015-09-25

### Added

- Officially support Python 3.5.
- Added `structlog.ReturnLogger.failure` and `structlog.PrintLogger.failure` as preparation for the new Twisted logging system.


### Fixed

- Tolerate frames without a `__name__`, better.
  [#58](https://github.com/hynek/structlog/pull/58)


## [15.2.0](https://github.com/hynek/structlog/compare/15.1.0...15.2.0) - 2015-06-10

### Added

- Added option to specify target key in `structlog.processors.TimeStamper` processor.
  [#51](https://github.com/hynek/structlog/pull/51)


### Changed

- Allow empty lists of processors.
  This is a valid use case since [#26](https://github.com/hynek/structlog/issues/26) has been merged.
  Before, supplying an empty list resulted in the defaults being used.
- Better support of `logging.Logger.exception` within `structlog`.
  [#52](https://github.com/hynek/structlog/pull/52)


### Fixed

- Prevent Twisted's `log.err` from quoting strings rendered by `structlog.twisted.JSONRenderer`.


## [15.1.0](https://github.com/hynek/structlog/compare/15.0.0...15.1.0) - 2015-02-24

### Fixed

- Tolerate frames without a `__name__` when guessing callsite names.


## [15.0.0](https://github.com/hynek/structlog/compare/0.4.2...15.0.0) - 2015-01-23

### Added

- Added `structlog.stdlib.add_log_level` and `structlog.stdlib.add_logger_name` processors.
  [#44](https://github.com/hynek/structlog/pull/44)
- Added `structlog.stdlib.BoundLogger.log`.
  [#42](https://github.com/hynek/structlog/pull/42)
- Added `structlog.stdlib.BoundLogger.exception`.
  [#22](https://github.com/hynek/structlog/pull/22)


### Changed

- Pass positional arguments to stdlib wrapped loggers that use string formatting.
  [#19](https://github.com/hynek/structlog/pull/19)
- `structlog` is now dually licensed under the [Apache License, Version 2](https://choosealicense.com/licenses/apache/) and the [MIT](https://choosealicense.com/licenses/mit/) license.
  Therefore it is now legal to use `structlog` with [GPLv2](https://choosealicense.com/licenses/gpl-2.0/)-licensed projects.
  [#28](https://github.com/hynek/structlog/pull/28)


## [0.4.2](https://github.com/hynek/structlog/compare/0.4.1...0.4.2) - 2014-07-26

### Removed

- Drop support for Python 3.2.
  There is no justification to add complexity for a Python version that nobody uses.
  If you are one of the [0.350%](https://alexgaynor.net/2014/jan/03/pypi-download-statistics/) that use Python 3.2, please stick to the 0.4 branch; critical bugs will still be fixed.


### Added

- Officially support Python 3.4.
- Allow final processor to return a dictionary.
  See the adapting chapter.
  [#26](https://github.com/hynek/structlog/issues/26)
- Test Twisted-related code on Python 3 (with some caveats).


### Fixed

- Fixed a memory leak in greenlet code that emulates thread locals.
  It shouldn't matter in practice unless you use multiple wrapped dicts within one program that is rather unlikely.
  [#8](https://github.com/hynek/structlog/pull/8)
- `structlog.PrintLogger` now is thread-safe.
- `from structlog import *` works now (but you still shouldn't use it).


## [0.4.1](https://github.com/hynek/structlog/compare/0.4.0...0.4.1) - 2013-12-19

### Changed

- Don't cache proxied methods in `structlog.threadlocal._ThreadLocalDictWrapper`. This doesn't affect regular users.


### Fixed

- Various doc fixes.


## [0.4.0](https://github.com/hynek/structlog/compare/0.3.2...0.4.0) - 2013-11-10

### Added

- Added `structlog.processors.StackInfoRenderer` for adding stack information to log entries without involving exceptions.
  Also added it to default processor chain.
  [#6](https://github.com/hynek/structlog/pull/6)
- Allow optional positional arguments for `structlog.get_logger` that are passed to logger factories.
  The standard library factory uses this for explicit logger naming.
  [#12](https://github.com/hynek/structlog/pull/12)
- Add `structlog.processors.ExceptionPrettyPrinter` for development and testing when multiline log entries aren't just acceptable but even helpful.
- Allow the standard library name guesser to ignore certain frame names.
  This is useful together with frameworks.
- Add meta data (e.g. function names, line numbers) extraction for wrapped stdlib loggers. [#5](https://github.com/hynek/structlog/pull/5)


## [0.3.2](https://github.com/hynek/structlog/compare/0.3.1...0.3.2) - 2013-09-27

### Fixed

- Fix stdlib's name guessing.


## [0.3.1](https://github.com/hynek/structlog/compare/0.3.0...0.3.1) - 2013-09-26

### Fixed

- Added forgotten `structlog.processors.TimeStamper` to API documentation.


## [0.3.0](https://github.com/hynek/structlog/compare/0.2.0...0.3.0) - 2013-09-23

### Changes:

- Greatly enhanced and polished the documentation and added a new theme based on Write The Docs, requests, and Flask.
- Add Python Standard Library-specific BoundLogger that has an explicit API instead of intercepting unknown method calls.
  See `structlog.stdlib.BoundLogger`.
- `structlog.ReturnLogger` now allows arbitrary positional and keyword arguments.
- Add Twisted-specific BoundLogger that has an explicit API instead of intercepting unknown method calls.
  See `structlog.twisted.BoundLogger`.
- Allow logger proxies that are returned by `structlog.get_logger` and `structlog.wrap_logger` to cache the BoundLogger they assemble according to configuration on first use.
  See the chapter on performance and the `cache_logger_on_first_use` argument of `structlog.configure` and `structlog.wrap_logger`.
- Extract a common base class for loggers that does nothing except keeping the context state.
  This makes writing custom loggers much easier and more straight-forward. See `structlog.BoundLoggerBase`.


## [0.2.0](https://github.com/hynek/structlog/compare/0.1.0...0.2.0) - 2013-09-17

### Added

- Add `key_order` option to `structlog.processors.KeyValueRenderer` for more predictable log entries with any `dict` class.
- Enhance Twisted support by offering JSONification of non-structlog log entries.
- Allow for custom serialization in `structlog.twisted.JSONRenderer` without abusing `__repr__`.


### Changed

- Promote to stable, thus henceforth a strict backwards-compatibility policy is put into effect.
- `structlog.PrintLogger` now uses proper I/O routines and is thus viable not only for examples but also for production.


## [0.1.0](https://github.com/hynek/structlog/tree/0.1.0) - 2013-09-16

Initial release.
