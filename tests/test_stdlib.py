# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.


import logging
import logging.config
import os
import sys

import pytest

from pretend import call_recorder

from structlog import ReturnLogger, configure, get_context, reset_defaults
from structlog.dev import ConsoleRenderer
from structlog.exceptions import DropEvent
from structlog.processors import JSONRenderer
from structlog.stdlib import (
    _NAME_TO_LEVEL,
    CRITICAL,
    WARN,
    BoundLogger,
    LoggerFactory,
    PositionalArgumentsFormatter,
    ProcessorFormatter,
    _FixedFindCallerLogger,
    add_log_level,
    add_log_level_number,
    add_logger_name,
    filter_by_level,
    get_logger,
    render_to_log_kwargs,
)

from .additional_frame import additional_frame


def build_bl(logger=None, processors=None, context=None):
    """
    Convenience function to build BoundLogger with sane defaults.
    """
    return BoundLogger(logger or ReturnLogger(), processors, {})


def return_method_name(_, method_name, __):
    """
    A final renderer that returns the name of the logging method.
    """
    return method_name


class TestLoggerFactory:
    def setup_method(self, method):
        """
        The stdlib logger factory modifies global state to fix caller
        identification.
        """
        self.original_logger = logging.getLoggerClass()

    def teardown_method(self, method):
        logging.setLoggerClass(self.original_logger)

    def test_deduces_correct_name(self):
        """
        The factory isn't called directly but from structlog._config so
        deducing has to be slightly smarter.
        """
        assert "tests.additional_frame" == (
            additional_frame(LoggerFactory()).name
        )
        assert "tests.test_stdlib" == LoggerFactory()().name

    def test_ignores_frames(self):
        """
        The name guesser walks up the frames until it reaches a frame whose
        name is not from structlog or one of the configurable other names.
        """
        assert (
            "__main__"
            == additional_frame(
                LoggerFactory(
                    ignore_frame_names=["tests.", "_pytest.", "pluggy"]
                )
            ).name
        )

    def test_deduces_correct_caller(self):
        logger = _FixedFindCallerLogger("test")
        file_name, line_number, func_name = logger.findCaller()[:3]

        assert file_name == os.path.realpath(__file__)
        assert func_name == "test_deduces_correct_caller"

    def test_stack_info(self):
        """
        If we ask for stack_info, it will returned.
        """
        logger = _FixedFindCallerLogger("test")
        testing, is_, fun, stack_info = logger.findCaller(stack_info=True)

        assert "testing, is_, fun" in stack_info

    def test_no_stack_info_by_default(self):
        logger = _FixedFindCallerLogger("test")
        testing, is_, fun, stack_info = logger.findCaller()

        assert None is stack_info

    def test_find_caller(self, monkeypatch):
        logger = LoggerFactory()()
        log_handle = call_recorder(lambda x: None)
        monkeypatch.setattr(logger, "handle", log_handle)
        logger.error("Test")
        log_record = log_handle.calls[0].args[0]

        assert log_record.funcName == "test_find_caller"
        assert log_record.name == __name__
        assert log_record.filename == os.path.basename(__file__)

    def test_sets_correct_logger(self):
        """
        Calling LoggerFactory ensures that Logger.findCaller gets patched.
        """
        LoggerFactory()

        assert logging.getLoggerClass() is _FixedFindCallerLogger

    def test_positional_argument_avoids_guessing(self):
        """
        If a positional argument is passed to the factory, it's used as the
        name instead of guessing.
        """
        lf = LoggerFactory()("foo")

        assert "foo" == lf.name


class TestFilterByLevel:
    def test_filters_lower_levels(self):
        """
        Log entries below the current level raise a DropEvent.
        """
        logger = logging.Logger(__name__)
        logger.setLevel(CRITICAL)

        with pytest.raises(DropEvent):
            filter_by_level(logger, "warn", {})

    def test_passes_higher_levels(self):
        """
        Log entries with higher levels are passed through unchanged.
        """
        logger = logging.Logger(__name__)
        logger.setLevel(WARN)
        event_dict = {"event": "test"}

        assert event_dict is filter_by_level(logger, "warn", event_dict)
        assert event_dict is filter_by_level(logger, "error", event_dict)
        assert event_dict is filter_by_level(logger, "exception", event_dict)


class TestBoundLogger:
    @pytest.mark.parametrize(
        ("method_name"), ["debug", "info", "warning", "error", "critical"]
    )
    def test_proxies_to_correct_method(self, method_name):
        """
        The basic proxied methods are proxied to the correct counterparts.
        """
        bl = BoundLogger(ReturnLogger(), [return_method_name], {})

        assert method_name == getattr(bl, method_name)("event")

    def test_proxies_exception(self):
        """
        BoundLogger.exception is proxied to Logger.error.
        """
        bl = BoundLogger(ReturnLogger(), [return_method_name], {})

        assert "error" == bl.exception("event")

    def test_proxies_log(self):
        """
        BoundLogger.exception.log() is proxied to the apropriate method.
        """
        bl = BoundLogger(ReturnLogger(), [return_method_name], {})

        assert "critical" == bl.log(50, "event")
        assert "debug" == bl.log(10, "event")

    def test_positional_args_proxied(self):
        """
        Positional arguments supplied are proxied as kwarg.
        """
        bl = BoundLogger(ReturnLogger(), [], {})
        args, kwargs = bl.debug("event", "foo", bar="baz")

        assert "baz" == kwargs.get("bar")
        assert ("foo",) == kwargs.get("positional_args")

    @pytest.mark.parametrize(
        "attribute_name",
        ["name", "level", "parent", "propagate", "handlers", "disabled"],
    )
    def test_stdlib_passthrough_attributes(self, attribute_name):
        """
        stdlib logger attributes are also available in stdlib BoundLogger.
        """
        stdlib_logger = logging.getLogger("Test")
        stdlib_logger_attribute = getattr(stdlib_logger, attribute_name)
        bl = BoundLogger(stdlib_logger, [], {})
        bound_logger_attribute = getattr(bl, attribute_name)

        assert bound_logger_attribute == stdlib_logger_attribute

    @pytest.mark.parametrize(
        "method_name,method_args",
        [
            ("addHandler", [None]),
            ("removeHandler", [None]),
            ("hasHandlers", None),
            ("callHandlers", [None]),
            ("handle", [None]),
            ("setLevel", [None]),
            ("getEffectiveLevel", None),
            ("isEnabledFor", [None]),
            ("findCaller", None),
            (
                "makeRecord",
                [
                    "name",
                    "debug",
                    "test_func",
                    "1",
                    "test msg",
                    ["foo"],
                    False,
                ],
            ),
            ("getChild", [None]),
        ],
    )
    def test_stdlib_passthrough_methods(self, method_name, method_args):
        """
        stdlib logger methods are also available in stdlib BoundLogger.
        """
        called_stdlib_method = [False]

        def validate(*args, **kw):
            called_stdlib_method[0] = True

        stdlib_logger = logging.getLogger("Test")
        stdlib_logger_method = getattr(stdlib_logger, method_name, None)
        if stdlib_logger_method:
            setattr(stdlib_logger, method_name, validate)
            bl = BoundLogger(stdlib_logger, [], {})
            bound_logger_method = getattr(bl, method_name)

            assert bound_logger_method is not None

            if method_args:
                bound_logger_method(*method_args)
            else:
                bound_logger_method()

            assert called_stdlib_method[0] is True

    def test_exception_exc_info(self):
        """
        BoundLogger.exception sets exc_info=True.
        """
        bl = BoundLogger(ReturnLogger(), [], {})

        assert ((), {"exc_info": True, "event": "event"}) == bl.exception(
            "event"
        )

    def test_exception_exc_info_override(self):
        """
        If *exc_info* is password to exception, it's used.
        """
        bl = BoundLogger(ReturnLogger(), [], {})

        assert ((), {"exc_info": 42, "event": "event"}) == bl.exception(
            "event", exc_info=42
        )

    def test_proxies_bind(self):
        """
        Bind calls the correct bind.
        """
        bl = build_bl().bind(a=42)

        assert {"a": 42} == get_context(bl)

    def test_proxies_new(self):
        """
        Newcalls the correct new.
        """
        bl = build_bl().bind(a=42).new(b=23)

        assert {"b": 23} == get_context(bl)

    def test_proxies_unbind(self):
        """
        Unbind calls the correct unbind.
        """
        bl = build_bl().bind(a=42).unbind("a")

        assert {} == get_context(bl)

    def test_proxies_try_unbind(self):
        """
        try_unbind calls the correct try_unbind.
        """
        bl = build_bl().bind(a=42).try_unbind("a", "b")

        assert {} == get_context(bl)


class TestPositionalArgumentsFormatter:
    def test_formats_tuple(self):
        """
        Positional arguments as simple types are rendered.
        """
        formatter = PositionalArgumentsFormatter()
        event_dict = formatter(
            None,
            None,
            {"event": "%d %d %s", "positional_args": (1, 2, "test")},
        )

        assert "1 2 test" == event_dict["event"]
        assert "positional_args" not in event_dict

    def test_formats_dict(self):
        """
        Positional arguments as dict are rendered.
        """
        formatter = PositionalArgumentsFormatter()
        event_dict = formatter(
            None,
            None,
            {"event": "%(foo)s bar", "positional_args": ({"foo": "bar"},)},
        )

        assert "bar bar" == event_dict["event"]
        assert "positional_args" not in event_dict

    def test_positional_args_retained(self):
        """
        Positional arguments are retained if remove_positional_args
        argument is set to False.
        """
        formatter = PositionalArgumentsFormatter(remove_positional_args=False)
        positional_args = (1, 2, "test")
        event_dict = formatter(
            None,
            None,
            {"event": "%d %d %s", "positional_args": positional_args},
        )

        assert "positional_args" in event_dict
        assert positional_args == event_dict["positional_args"]

    def test_nop_no_args(self):
        """
        If no positional args are passed, nothing happens.
        """
        formatter = PositionalArgumentsFormatter()

        assert {} == formatter(None, None, {})

    def test_args_removed_if_empty(self):
        """
        If remove_positional_args is True and positional_args is (), still
        remove them.

        Regression test for https://github.com/hynek/structlog/issues/82.
        """
        formatter = PositionalArgumentsFormatter()

        assert {} == formatter(None, None, {"positional_args": ()})


class TestAddLogLevelNumber:
    @pytest.mark.parametrize("level, number", _NAME_TO_LEVEL.items())
    def test_log_level_number_added(self, level, number):
        """
        The log level number is added to the event dict.
        """
        event_dict = add_log_level_number(None, level, {})

        assert number == event_dict["level_number"]


class TestAddLogLevel:
    def test_log_level_added(self):
        """
        The log level is added to the event dict.
        """
        event_dict = add_log_level(None, "error", {})

        assert "error" == event_dict["level"]

    def test_log_level_alias_normalized(self):
        """
        The normalized name of the log level is added to the event dict.
        """
        event_dict = add_log_level(None, "warn", {})

        assert "warning" == event_dict["level"]


@pytest.fixture
def log_record():
    """
    A LogRecord factory.
    """

    def create_log_record(**kwargs):
        defaults = {
            "name": "sample-name",
            "level": logging.INFO,
            "pathname": None,
            "lineno": None,
            "msg": "sample-message",
            "args": [],
            "exc_info": None,
        }
        defaults.update(kwargs)
        return logging.LogRecord(**defaults)

    return create_log_record


class TestAddLoggerName:
    def test_logger_name_added(self):
        """
        The logger name is added to the event dict.
        """
        name = "sample-name"
        logger = logging.getLogger(name)
        event_dict = add_logger_name(logger, None, {})

        assert name == event_dict["logger"]

    def test_logger_name_added_with_record(self, log_record):
        """
        The logger name is deduced from the LogRecord if provided.
        """
        name = "sample-name"
        record = log_record(name=name)
        event_dict = add_logger_name(None, None, {"_record": record})

        assert name == event_dict["logger"]


class TestRenderToLogKW:
    def test_default(self):
        """
        Translates `event` to `msg` and handles otherwise empty `event_dict`s.
        """
        d = render_to_log_kwargs(None, None, {"event": "message"})

        assert {"msg": "message", "extra": {}} == d

    def test_add_extra_event_dict(self, event_dict):
        """
        Adds all remaining data from `event_dict` into `extra`.
        """
        event_dict["event"] = "message"
        d = render_to_log_kwargs(None, None, event_dict)

        assert {"msg": "message", "extra": event_dict} == d


@pytest.fixture
def configure_for_pf():
    """
    Configure structlog to use ProcessorFormatter.

    Reset both structlog and logging setting after the test.
    """
    configure(
        processors=[add_log_level, ProcessorFormatter.wrap_for_formatter],
        logger_factory=LoggerFactory(),
        wrapper_class=BoundLogger,
    )

    yield

    logging.basicConfig()
    reset_defaults()


def configure_logging(pre_chain, logger=None, pass_foreign_args=False):
    """
    Configure logging to use ProcessorFormatter.
    """
    return logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "plain": {
                    "()": ProcessorFormatter,
                    "processor": ConsoleRenderer(colors=False),
                    "foreign_pre_chain": pre_chain,
                    "format": "%(message)s [in %(funcName)s]",
                    "logger": logger,
                    "pass_foreign_args": pass_foreign_args,
                }
            },
            "handlers": {
                "default": {
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                    "formatter": "plain",
                }
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": "DEBUG",
                    "propagate": True,
                }
            },
        }
    )


class TestProcessorFormatter:
    """
    These are all integration tests because they're all about integration.
    """

    def test_foreign_delegate(self, configure_for_pf, capsys):
        """
        If foreign_pre_chain is None, non-structlog log entries are delegated
        to logging.
        """
        configure_logging(None)

        logging.getLogger().warning("foo")

        assert ("", "foo [in test_foreign_delegate]\n") == capsys.readouterr()

    def test_clears_args(self, configure_for_pf, capsys):
        """
        We render our log records before sending it back to logging.  Therefore
        we must clear `LogRecord.args` otherwise the user gets an
        `TypeError: not all arguments converted during string formatting.` if
        they use positional formatting in stdlib logging.
        """
        configure_logging(None)

        logging.getLogger().warning("hello %s.", "world")

        assert (
            "",
            "hello world. [in test_clears_args]\n",
        ) == capsys.readouterr()

    def test_pass_foreign_args_true_sets_positional_args_key(
        self, configure_for_pf, capsys
    ):
        """
        If `pass_foreign_args` is `True` we set the `positional_args` key in
        the `event_dict` before clearing args.
        """
        test_processor = call_recorder(lambda l, m, event_dict: event_dict)
        configure_logging((test_processor,), pass_foreign_args=True)

        positional_args = {"foo": "bar"}
        logging.getLogger().info("okay %(foo)s", positional_args)

        event_dict = test_processor.calls[0].args[2]

        assert "positional_args" in event_dict
        assert positional_args == event_dict["positional_args"]

    def test_log_dict(self, configure_for_pf, capsys):
        """
        Test that dicts can be logged with std library loggers.
        """
        configure_logging(None)

        logging.getLogger().warning({"foo": "bar"})

        assert (
            "",
            "{'foo': 'bar'} [in test_log_dict]\n",
        ) == capsys.readouterr()

    def test_foreign_pre_chain(self, configure_for_pf, capsys):
        """
        If foreign_pre_chain is an iterable, it's used to pre-process
        non-structlog log entries.
        """
        configure_logging((add_log_level,))

        logging.getLogger().warning("foo")

        assert (
            "",
            "[warning  ] foo [in test_foreign_pre_chain]\n",
        ) == capsys.readouterr()

    def test_foreign_pre_chain_add_logger_name(self, configure_for_pf, capsys):
        """
        foreign_pre_chain works with add_logger_name processor.
        """
        configure_logging((add_logger_name,))

        logging.getLogger("sample-name").warning("foo")

        assert (
            "",
            "foo                            [sample-name]  [in test_foreign_pr"
            "e_chain_add_logger_name]\n",
        ) == capsys.readouterr()

    def test_foreign_chain_can_pass_dictionaries_without_excepting(
        self, configure_for_pf, capsys
    ):
        """
        If a foreign logger passes a dictionary to a logging function,
        check we correctly identify that it did not come from structlog.
        """
        configure_logging(None)
        configure(
            processors=[ProcessorFormatter.wrap_for_formatter],
            logger_factory=LoggerFactory(),
            wrapper_class=BoundLogger,
        )

        logging.getLogger().warning({"foo": "bar"})

        assert (
            "",
            "{'foo': 'bar'} [in "
            "test_foreign_chain_can_pass_dictionaries_without_excepting]\n",
        ) == capsys.readouterr()

    def test_foreign_pre_chain_gets_exc_info(self, configure_for_pf, capsys):
        """
        If non-structlog record contains exc_info, foreign_pre_chain functions
        have access to it.
        """
        test_processor = call_recorder(lambda l, m, event_dict: event_dict)
        configure_logging((test_processor,))

        try:
            raise RuntimeError("oh noo")
        except Exception:
            logging.getLogger().exception("okay")

        event_dict = test_processor.calls[0].args[2]

        assert "exc_info" in event_dict
        assert isinstance(event_dict["exc_info"], tuple)

    def test_foreign_pre_chain_sys_exc_info(self, configure_for_pf, capsys):
        """
        If a foreign_pre_chain function accesses sys.exc_info(),
        ProcessorFormatter should not have changed it.
        """

        class MyException(Exception):
            pass

        def add_excinfo(logger, log_method, event_dict):
            event_dict["exc_info"] = sys.exc_info()
            return event_dict

        test_processor = call_recorder(lambda l, m, event_dict: event_dict)
        configure_logging((add_excinfo, test_processor))

        try:
            raise MyException("oh noo")
        except Exception:
            logging.getLogger().error("okay")

        event_dict = test_processor.calls[0].args[2]

        assert MyException is event_dict["exc_info"][0]

    def test_other_handlers_get_original_record(
        self, configure_for_pf, capsys
    ):
        """
        Logging handlers that come after the handler with ProcessorFormatter
        should receive original, unmodified record.
        """
        configure_logging(None)

        handler1 = logging.StreamHandler()
        handler1.setFormatter(ProcessorFormatter(JSONRenderer()))
        handler2 = type("", (), {})()
        handler2.handle = call_recorder(lambda record: None)
        handler2.level = logging.INFO
        logger = logging.getLogger()
        logger.addHandler(handler1)
        logger.addHandler(handler2)

        logger.info("meh")

        assert 1 == len(handler2.handle.calls)

        handler2_record = handler2.handle.calls[0].args[0]

        assert "meh" == handler2_record.msg

    @pytest.mark.parametrize("keep", [True, False])
    def test_formatter_unsets_exc_info(self, configure_for_pf, capsys, keep):
        """
        Stack traces doesn't get printed outside of the json document when
        keep_exc_info are set to False but preserved if set to True.
        """
        configure_logging(None)
        logger = logging.getLogger()

        def format_exc_info_fake(logger, name, event_dict):
            del event_dict["exc_info"]
            event_dict["exception"] = "Exception!"
            return event_dict

        formatter = ProcessorFormatter(
            processor=JSONRenderer(),
            keep_stack_info=keep,
            keep_exc_info=keep,
            foreign_pre_chain=[format_exc_info_fake],
        )
        logger.handlers[0].setFormatter(formatter)

        try:
            raise RuntimeError("oh noo")
        except Exception:
            logging.getLogger().exception("seen worse")

        out, err = capsys.readouterr()

        assert "" == out

        if keep is False:
            assert (
                '{"event": "seen worse", "exception": "Exception!"}\n'
            ) == err
        else:
            assert "Traceback (most recent call last):" in err

    @pytest.mark.parametrize("keep", [True, False])
    def test_formatter_unsets_stack_info(self, configure_for_pf, capsys, keep):
        """
        Stack traces doesn't get printed outside of the json document when
        keep_stack_info are set to False but preserved if set to True.
        """
        configure_logging(None)
        logger = logging.getLogger()

        formatter = ProcessorFormatter(
            processor=JSONRenderer(),
            keep_stack_info=keep,
            keep_exc_info=keep,
            foreign_pre_chain=[],
        )
        logger.handlers[0].setFormatter(formatter)

        logging.getLogger().warning("have a stack trace", stack_info=True)

        out, err = capsys.readouterr()

        assert "" == out

        if keep is False:
            assert 1 == err.count("Stack (most recent call last):")
        else:
            assert 2 == err.count("Stack (most recent call last):")

    def test_native(self, configure_for_pf, capsys):
        """
        If the log entry comes from structlog, it's unpackaged and processed.
        """
        configure_logging(None)

        get_logger().warning("foo")

        assert (
            "",
            "[warning  ] foo [in test_native]\n",
        ) == capsys.readouterr()

    def test_native_logger(self, configure_for_pf, capsys):
        """
        If the log entry comes from structlog, it's unpackaged and processed.
        """
        logger = logging.getLogger()
        configure_logging(None, logger=logger)

        get_logger().warning("foo")

        assert (
            "",
            "[warning  ] foo [in test_native_logger]\n",
        ) == capsys.readouterr()

    def test_foreign_pre_chain_filter_by_level(self, configure_for_pf, capsys):
        """
        foreign_pre_chain works with filter_by_level processor.
        """
        logger = logging.getLogger()
        configure_logging((filter_by_level,), logger=logger)
        configure(
            processors=[ProcessorFormatter.wrap_for_formatter],
            logger_factory=LoggerFactory(),
            wrapper_class=BoundLogger,
        )

        logger.warning("foo")

        assert (
            "",
            "foo [in test_foreign_pre_chain_filter_by_level]\n",
        ) == capsys.readouterr()
