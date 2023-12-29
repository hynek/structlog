# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import pickle
import sys

from io import StringIO
from unittest import mock

import pytest

from structlog import dev


class TestPad:
    def test_normal(self):
        """
        If chars are missing, adequate number of " " are added.
        """
        assert 100 == len(dev._pad("test", 100))

    def test_negative(self):
        """
        If string is already too long, don't do anything.
        """
        assert len("test") == len(dev._pad("test", 2))


@pytest.fixture(name="cr", scope="session")
def _cr():
    return dev.ConsoleRenderer(
        colors=dev._has_colors, exception_formatter=dev.plain_traceback
    )


@pytest.fixture(name="styles", scope="session")
def _styles(cr):
    return cr._styles


@pytest.fixture(name="padded", scope="session")
def _padded(styles):
    return styles.bright + dev._pad("test", dev._EVENT_WIDTH) + styles.reset


class TestConsoleRenderer:
    @pytest.mark.skipif(dev.colorama, reason="Colorama must be missing.")
    @pytest.mark.skipif(
        not dev._IS_WINDOWS, reason="Must be running on Windows."
    )
    def test_missing_colorama(self):
        """
        ConsoleRenderer(colors=True) raises SystemError on initialization if
        Colorama is missing and _IS_WINDOWS is True.
        """
        with pytest.raises(SystemError) as e:
            dev.ConsoleRenderer(colors=True)

        assert (
            "ConsoleRenderer with `colors=True` requires the Colorama package "
            "installed."
        ) in e.value.args[0]

    def test_plain(self, cr, padded):
        """
        Works with a plain event_dict with only the event.
        """
        rv = cr(None, None, {"event": "test"})

        assert padded == rv

    def test_timestamp(self, cr, styles, padded):
        """
        Timestamps get prepended.
        """
        rv = cr(None, None, {"event": "test", "timestamp": 42})

        assert (styles.timestamp + "42" + styles.reset + " " + padded) == rv

    def test_event_stringified(self, cr, padded):
        """
        Event is cast to string.
        """
        not_a_string = Exception("test")

        rv = cr(None, None, {"event": not_a_string})

        assert padded == rv

    def test_event_renamed(self):
        """
        The main event key can be renamed.
        """
        cr = dev.ConsoleRenderer(colors=False, event_key="msg")

        assert "new event name                 event=something custom" == cr(
            None, None, {"msg": "new event name", "event": "something custom"}
        )

    def test_timestamp_renamed(self):
        """
        The timestamp key can be renamed.
        """
        cr = dev.ConsoleRenderer(colors=False, timestamp_key="ts")

        assert (
            "2023-09-07 le event"
            == cr(
                None,
                None,
                {"ts": "2023-09-07", "event": "le event"},
            ).rstrip()
        )

    def test_level(self, cr, styles, padded):
        """
        Levels are rendered aligned, in square brackets, and color-coded.
        """
        rv = cr(
            None, None, {"event": "test", "level": "critical", "foo": "bar"}
        )

        assert (
            "["
            + dev.RED
            + styles.bright
            + dev._pad("critical", cr._longest_level)
            + styles.reset
            + "] "
            + padded
            + " "
            + styles.kv_key
            + "foo"
            + styles.reset
            + "="
            + styles.kv_value
            + "bar"
            + styles.reset
        ) == rv

    def test_init_accepts_overriding_levels(self, styles, padded):
        """
        Stdlib levels are rendered aligned, in brackets, and color coded.
        """
        my_styles = dev.ConsoleRenderer.get_default_level_styles(
            colors=dev._has_colors
        )
        my_styles["MY_OH_MY"] = my_styles["critical"]
        cr = dev.ConsoleRenderer(
            colors=dev._has_colors, level_styles=my_styles
        )

        # this would blow up if the level_styles override failed
        rv = cr(
            None, None, {"event": "test", "level": "MY_OH_MY", "foo": "bar"}
        )

        assert (
            "["
            + dev.RED
            + styles.bright
            + dev._pad("MY_OH_MY", cr._longest_level)
            + styles.reset
            + "] "
            + padded
            + " "
            + styles.kv_key
            + "foo"
            + styles.reset
            + "="
            + styles.kv_value
            + "bar"
            + styles.reset
        ) == rv

    def test_logger_name(self, cr, styles, padded):
        """
        Logger names are appended after the event.
        """
        rv = cr(None, None, {"event": "test", "logger": "some_module"})

        assert (
            padded
            + " ["
            + styles.reset
            + styles.bright
            + dev.BLUE
            + "some_module"
            + styles.reset
            + "]"
            + styles.reset
        ) == rv

    def test_logger_name_name(self, cr, padded, styles):
        """
        It's possible to set the logger name using a "logger_name" key.
        """
        assert (
            padded
            + " ["
            + styles.reset
            + styles.bright
            + dev.BLUE
            + "yolo"
            + styles.reset
            + "]"
            + styles.reset
        ) == cr(None, None, {"event": "test", "logger_name": "yolo"})

    def test_key_values(self, cr, styles, padded):
        """
        Key-value pairs go sorted alphabetically to the end.
        """
        rv = cr(None, None, {"event": "test", "key": "value", "foo": "bar"})

        assert (
            padded
            + " "
            + styles.kv_key
            + "foo"
            + styles.reset
            + "="
            + styles.kv_value
            + "bar"
            + styles.reset
            + " "
            + styles.kv_key
            + "key"
            + styles.reset
            + "="
            + styles.kv_value
            + "value"
            + styles.reset
        ) == rv

    def test_key_values_unsorted(self, styles, padded):
        """
        Key-value pairs go in original order to the end.
        """
        cr = dev.ConsoleRenderer(sort_keys=False)

        rv = cr(
            None,
            None,
            {"event": "test", "key": "value", "foo": "bar"},
        )

        assert (
            padded
            + " "
            + styles.kv_key
            + "key"
            + styles.reset
            + "="
            + styles.kv_value
            + "value"
            + styles.reset
            + " "
            + styles.kv_key
            + "foo"
            + styles.reset
            + "="
            + styles.kv_value
            + "bar"
            + styles.reset
        ) == rv

    @pytest.mark.parametrize("wrap", [True, False])
    def test_exception_rendered(
        self, cr, recwarn, wrap, styles, padded, monkeypatch
    ):
        """
        Exceptions are rendered after a new line if they are already rendered
        in the event dict.

        A warning is emitted if exception printing is "customized".
        """
        exc = "Traceback:\nFake traceback...\nFakeError: yolo"

        # Wrap the formatter to provoke the warning.
        if wrap:
            monkeypatch.setattr(
                cr,
                "_exception_formatter",
                lambda s, ei: dev.plain_traceback(s, ei),
            )

        rv = cr(None, None, {"event": "test", "exception": exc})

        assert (f"{padded}\n" + exc) == rv

        if wrap:
            (w,) = recwarn.list
            assert (
                "Remove `format_exc_info` from your processor chain "
                "if you want pretty exceptions.",
            ) == w.message.args

    def test_stack_info(self, cr, styles, padded):
        """
        Stack traces are rendered after a new line.
        """
        stack = "fake stack"
        rv = cr(None, None, {"event": "test", "stack": stack})

        assert (f"{padded}\n" + stack) == rv

    def test_exc_info_tuple(self, cr, styles, padded):
        """
        If exc_info is a tuple, it is used.
        """

        try:
            0 / 0
        except ZeroDivisionError:
            ei = sys.exc_info()

        rv = cr(None, None, {"event": "test", "exc_info": ei})

        exc = dev._format_exception(ei)

        assert (f"{padded}\n" + exc) == rv

    def test_exc_info_bool(self, cr, styles, padded):
        """
        If exc_info is True, it is obtained using sys.exc_info().
        """

        try:
            0 / 0
        except ZeroDivisionError:
            ei = sys.exc_info()
            rv = cr(None, None, {"event": "test", "exc_info": True})

        exc = dev._format_exception(ei)

        assert (f"{padded}\n" + exc) == rv

    def test_exc_info_exception(self, cr, styles, padded):
        """
        If exc_info is an exception, it is used by converting to a tuple.
        """

        try:
            0 / 0
        except ZeroDivisionError as e:
            ei = e

        rv = cr(None, None, {"event": "test", "exc_info": ei})

        exc = dev._format_exception((ei.__class__, ei, ei.__traceback__))

        assert (f"{padded}\n" + exc) == rv

    def test_pad_event_param(self, styles):
        """
        `pad_event` parameter works.
        """
        rv = dev.ConsoleRenderer(42, dev._has_colors)(
            None, None, {"event": "test", "foo": "bar"}
        )

        assert (
            styles.bright
            + dev._pad("test", 42)
            + styles.reset
            + " "
            + styles.kv_key
            + "foo"
            + styles.reset
            + "="
            + styles.kv_value
            + "bar"
            + styles.reset
        ) == rv

    @pytest.mark.parametrize("explicit_ei", ["tuple", "exception", False])
    def test_everything(self, cr, styles, padded, explicit_ei):
        """
        Put all cases together.
        """
        if explicit_ei:
            try:
                0 / 0
            except ZeroDivisionError as e:
                if explicit_ei == "tuple":
                    ei = sys.exc_info()
                elif explicit_ei == "exception":
                    ei = e
                else:
                    raise ValueError from None
        else:
            ei = True

        stack = "fake stack trace"
        ed = {
            "event": "test",
            "exc_info": ei,
            "key": "value",
            "foo": "bar",
            "timestamp": "13:13",
            "logger": "some_module",
            "level": "error",
            "stack": stack,
        }

        if explicit_ei:
            rv = cr(None, None, ed)
        else:
            try:
                0 / 0
            except ZeroDivisionError:
                rv = cr(None, None, ed)
                ei = sys.exc_info()

        if isinstance(ei, BaseException):
            ei = (ei.__class__, ei, ei.__traceback__)

        exc = dev._format_exception(ei)

        assert (
            styles.timestamp
            + "13:13"
            + styles.reset
            + " ["
            + styles.level_error
            + styles.bright
            + dev._pad("error", cr._longest_level)
            + styles.reset
            + "] "
            + padded
            + " ["
            + styles.reset
            + styles.bright
            + dev.BLUE
            + "some_module"
            + styles.reset
            + "]"
            + styles.reset
            + " "
            + styles.kv_key
            + "foo"
            + styles.reset
            + "="
            + styles.kv_value
            + "bar"
            + styles.reset
            + " "
            + styles.kv_key
            + "key"
            + styles.reset
            + "="
            + styles.kv_value
            + "value"
            + styles.reset
            + "\n"
            + stack
            + "\n\n"
            + "=" * 79
            + "\n"
            + "\n"
            + exc
        ) == rv

    def test_colorama_colors_false(self):
        """
        If colors is False, don't use colors or styles ever.
        """
        plain_cr = dev.ConsoleRenderer(colors=False)

        rv = plain_cr(
            None, None, {"event": "event", "level": "info", "foo": "bar"}
        )

        assert dev._PlainStyles is plain_cr._styles
        assert "[info     ] event                          foo=bar" == rv

    def test_colorama_force_colors(self, styles, padded):
        """
        If force_colors is True, use colors even if the destination is non-tty.
        """
        cr = dev.ConsoleRenderer(
            colors=dev._has_colors, force_colors=dev._has_colors
        )

        rv = cr(
            None, None, {"event": "test", "level": "critical", "foo": "bar"}
        )

        assert (
            "["
            + dev.RED
            + styles.bright
            + dev._pad("critical", cr._longest_level)
            + styles.reset
            + "] "
            + padded
            + " "
            + styles.kv_key
            + "foo"
            + styles.reset
            + "="
            + styles.kv_value
            + "bar"
            + styles.reset
        ) == rv

        assert not dev._has_colors or dev._ColorfulStyles is cr._styles

    @pytest.mark.parametrize("rns", [True, False])
    def test_repr_native_str(self, rns):
        """
        repr_native_str=False doesn't repr on native strings.  "event" is
        never repr'ed.
        """
        rv = dev.ConsoleRenderer(colors=False, repr_native_str=rns)(
            None, None, {"event": "哈", "key": 42, "key2": "哈"}
        )

        cnt = rv.count("哈")

        assert 2 == cnt

    @pytest.mark.parametrize("repr_native_str", [True, False])
    @pytest.mark.parametrize("force_colors", [True, False])
    @pytest.mark.parametrize("proto", range(pickle.HIGHEST_PROTOCOL + 1))
    def test_pickle(self, repr_native_str, force_colors, proto):
        """
        ConsoleRenderer can be pickled and unpickled.
        """
        r = dev.ConsoleRenderer(
            repr_native_str=repr_native_str, force_colors=force_colors
        )

        assert r(None, None, {"event": "foo"}) == pickle.loads(
            pickle.dumps(r, proto)
        )(None, None, {"event": "foo"})

    def test_no_exception(self):
        """
        If there is no exception, don't blow up.
        """
        r = dev.ConsoleRenderer(colors=False)

        assert (
            "hi"
            == r(
                None, None, {"event": "hi", "exc_info": (None, None, None)}
            ).rstrip()
        )

    def test_columns_warns_about_meaningless_arguments(self, recwarn):
        """
        If columns is set, a warning is emitted for all ignored arguments.
        """
        dev.ConsoleRenderer(
            columns=[dev.Column("", lambda k, v: "")],
            pad_event=42,
            colors=not dev._has_colors,
            force_colors=True,
            repr_native_str=True,
            level_styles=dev._PlainStyles,
            event_key="not event",
            timestamp_key="not timestamp",
        )

        assert {
            f"The `{arg}` argument is ignored when passing `columns`."
            for arg in (
                "pad_event",
                "colors",
                "force_colors",
                "repr_native_str",
                "level_styles",
                "event_key",
                "timestamp_key",
            )
        } == {str(w.message) for w in recwarn.list}

    def test_detects_default_column(self):
        """
        The default renderer is detected and removed from the columns list.
        """
        fake_formatter = object()
        llcf = dev.Column("log_level", dev.LogLevelColumnFormatter(None, ""))

        cr = dev.ConsoleRenderer(
            columns=[dev.Column("", fake_formatter), llcf]
        )

        assert fake_formatter is cr._default_column_formatter
        assert [llcf] == cr._columns

    def test_enforces_presence_of_exactly_one_default_formatter(self):
        """
        If there is no, or more than one, default formatter, raise ValueError.
        """
        with pytest.raises(
            ValueError,
            match="Must pass a default column formatter",
        ):
            dev.ConsoleRenderer(columns=[])

        with pytest.raises(
            ValueError,
            match="Only one default column formatter allowed.",
        ):
            dev.ConsoleRenderer(
                columns=[
                    dev.Column("", lambda k, v: ""),
                    dev.Column("", lambda k, v: ""),
                ]
            )


class TestSetExcInfo:
    def test_wrong_name(self):
        """
        Do nothing if name is not exception.
        """
        assert {} == dev.set_exc_info(None, "foo", {})

    @pytest.mark.parametrize("ei", [False, None, ()])
    def test_already_set(self, ei):
        """
        Do nothing if exc_info is already set.
        """
        assert {"exc_info": ei} == dev.set_exc_info(
            None, "foo", {"exc_info": ei}
        )

    def test_set_it(self):
        """
        Set exc_info to True if its not set and if the method name is
        exception.
        """
        assert {"exc_info": True} == dev.set_exc_info(None, "exception", {})


@pytest.mark.skipif(dev.rich is None, reason="Needs Rich.")
class TestRichTracebackFormatter:
    def test_default(self):
        """
        If Rich is present, it's the default.
        """
        assert dev.default_exception_formatter is dev.rich_traceback

    def test_does_not_blow_up(self, sio):
        """
        We trust Rich to do the right thing, so we just exercise the function
        and check the first new line that we add manually is present.
        """
        try:
            0 / 0
        except ZeroDivisionError:
            dev.rich_traceback(sio, sys.exc_info())

        assert sio.getvalue().startswith("\n")

    def test_width_minus_one(self, sio):
        """
        If width is -1, it's replaced by the terminal width on first use.
        """
        rtf = dev.RichTracebackFormatter(width=-1)

        with mock.patch("shutil.get_terminal_size", return_value=(42, 0)):
            try:
                0 / 0
            except ZeroDivisionError:
                rtf(sio, sys.exc_info())

        assert 42 == rtf.width


@pytest.mark.skipif(
    dev.better_exceptions is None, reason="Needs better-exceptions."
)
class TestBetterTraceback:
    def test_default(self):
        """
        If better-exceptions is present and Rich is NOT present, it's the
        default.
        """
        assert (
            dev.rich is not None
            or dev.default_exception_formatter is dev.better_traceback
        )

    def test_does_not_blow_up(self):
        """
        We trust better-exceptions to do the right thing, so we just exercise
        the function.
        """
        sio = StringIO()
        try:
            0 / 0
        except ZeroDivisionError:
            dev.better_traceback(sio, sys.exc_info())

        assert sio.getvalue().startswith("\n")


class TestLogLevelColumnFormatter:
    def test_no_style(self):
        """
        No level_styles means no control characters and no padding.
        """
        assert "[critical]" == dev.LogLevelColumnFormatter(None, "foo")(
            "", "critical"
        )
