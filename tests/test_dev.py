# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import absolute_import, division, print_function

import pytest

from structlog import dev


class TestPad(object):
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


@pytest.mark.skipif(dev.colorama is not None,
                    reason="Colorama must be missing.")
def test_missing_colorama():
    """
    ConsoleRenderer() raises SystemError on initialization if colorama is
    missing.

    This is a function such that TestConsoleRenderer can be protected on class
    level.
    """
    with pytest.raises(SystemError) as e:
        dev.ConsoleRenderer()

    assert (
        "ConsoleRenderer requires the colorama package installed."
    ) in e.value.args[0]


@pytest.fixture
def cr_c():
    return dev.ConsoleRenderer(colorize=True)


@pytest.fixture
def cr_nc():
    return dev.ConsoleRenderer(colorize=False)


if dev.colorama is not None:
    PADDED_TEST_COLOR = (
        dev.BRIGHT +
        dev._pad("test", dev._EVENT_WIDTH) +
        dev.RESET_ALL + " "
    )
PADDED_TEST_NO_COLOR = dev._pad("test", dev._EVENT_WIDTH) + " "


@pytest.mark.skipif(dev.colorama is None, reason="Requires colorama.")
class TestConsoleRenderer(object):
    def test_plain__color(self, cr_c):
        """
        Works with a plain event_dict with only the event.
        """
        rv = cr_c(None, None, {"event": "test"})

        assert PADDED_TEST_COLOR == rv

    def test_plain__no_color(self, cr_nc):
        """
        Works with a plain event_dict with only the event.
        """
        rv = cr_nc(None, None, {"event": "test"})

        assert PADDED_TEST_NO_COLOR == rv

    def test_timestamp__color(self, cr_c):
        """
        Timestamps get prepended dimmed..
        """
        rv = cr_c(None, None, {"event": "test", "timestamp": 42})

        assert (
            dev.DIM + "42" + dev.RESET_ALL +
            " " + PADDED_TEST_COLOR
        ) == rv

    def test_timestamp__no_color(self, cr_nc):
        """
        Timestamps not get prepended dimmed..
        """
        rv = cr_nc(None, None, {"event": "test", "timestamp": 42})

        assert (
            "42 " + PADDED_TEST_NO_COLOR
        ) == rv

    def test_level__color(self, cr_c):
        """
        Levels are rendered aligned, in square brackets, and color coded.
        """
        rv = cr_c(None, None, {"event": "test", "level": "critical"})

        assert (
            "[" + dev.RED + dev.BRIGHT +
            dev._pad("critical", cr_c._longest_level) +
            dev.RESET_ALL + "] " +
            PADDED_TEST_COLOR
        ) == rv

    def test_level__no_color(self, cr_nc):
        """
        Levels are rendered aligned, in square brackets, and not color coded.
        """
        rv = cr_nc(None, None, {"event": "test", "level": "critical"})

        assert (
            "[" +
            dev._pad("critical", cr_nc._longest_level) +
            "] " +
            PADDED_TEST_NO_COLOR
        ) == rv

    def test_logger_name__color(self, cr_c):
        """
        Logger names are appended after the event with color.
        """
        rv = cr_c(None, None, {"event": "test", "logger": "some_module"})

        assert (
            PADDED_TEST_COLOR +
            "[" + dev.BLUE + dev.BRIGHT +
            "some_module" +
            dev.RESET_ALL + "] "
        ) == rv

    def test_logger_name__no_color(self, cr_nc):
        """
        Logger names are appended after the event without color.
        """
        rv = cr_nc(None, None, {"event": "test", "logger": "some_module"})

        assert (
            PADDED_TEST_NO_COLOR + "[some_module] "
        ) == rv

    def test_key_values__color(self, cr_c):
        """
        Key-value pairs go sorted alphabetically to the end with color.
        """
        rv = cr_c(None, None, {
            "event": "test",
            "key": "value",
            "foo": "bar",
        })
        assert (
            PADDED_TEST_COLOR +
            dev.CYAN + "foo" + dev.RESET_ALL + "=" + dev.MAGENTA + "'bar'" +
            dev.RESET_ALL + " " +
            dev.CYAN + "key" + dev.RESET_ALL + "=" + dev.MAGENTA + "'value'" +
            dev.RESET_ALL
        ) == rv

    def test_key_values__no_color(self, cr_nc):
        """
        Key-value pairs go sorted alphabetically to the end without color.
        """
        rv = cr_nc(None, None, {
            "event": "test",
            "key": "value",
            "foo": "bar",
        })
        assert (
            PADDED_TEST_NO_COLOR + "foo='bar' key='value'"
        ) == rv

    def test_exception__color(self, cr_c):
        """
        Exceptions are rendered after a new line.
        """
        exc = "Traceback:\nFake traceback...\nFakeError: yolo"

        rv = cr_c(None, None, {
            "event": "test",
            "exception": exc
        })

        assert (
            PADDED_TEST_COLOR + "\n" + exc
        ) == rv

    def test_exception__no_color(self, cr_nc):
        """
        Exceptions are rendered after a new line.
        """
        exc = "Traceback:\nFake traceback...\nFakeError: yolo"

        rv = cr_nc(None, None, {
            "event": "test",
            "exception": exc
        })

        assert (
            PADDED_TEST_NO_COLOR + "\n" + exc
        ) == rv

    def test_stack_info__color(self, cr_c):
        """
        Stack traces are rendered after a new line.
        """
        stack = "fake stack"
        rv = cr_c(None, None, {
            "event": "test",
            "stack": stack
        })

        assert (
            PADDED_TEST_COLOR + "\n" + stack
        ) == rv

    def test_stack_info__no_color(self, cr_nc):
        """
        Stack traces are rendered after a new line.
        """
        stack = "fake stack"
        rv = cr_nc(None, None, {
            "event": "test",
            "stack": stack
        })

        assert (
            PADDED_TEST_NO_COLOR + "\n" + stack
        ) == rv

    def test_pad_event_param__color(self):
        """
        `pad_event` parameter works.
        """
        rv = dev.ConsoleRenderer(42, True)(None, None, {"event": "test"})

        assert (
            dev.BRIGHT +
            dev._pad("test", 42) +
            dev.RESET_ALL + " "
        ) == rv

    def test_pad_event_param__no_color(self):
        """
        `pad_event` parameter works.
        """
        rv = dev.ConsoleRenderer(42, False)(None, None, {"event": "test"})

        assert (
            dev._pad("test", 42) + " "
        ) == rv

    def test_everything__color(self, cr_c):
        """
        Put all cases together.
        """
        exc = "Traceback:\nFake traceback...\nFakeError: yolo"
        stack = "fake stack trace"

        rv = cr_c(None, None, {
            "event": "test",
            "exception": exc,
            "key": "value",
            "foo": "bar",
            "timestamp": "13:13",
            "logger": "some_module",
            "level": "error",
            "stack": stack,
        })

        assert (
            dev.DIM + "13:13" + dev.RESET_ALL +
            " [" + dev.RED + dev.BRIGHT +
            dev._pad("error", cr_c._longest_level) +
            dev.RESET_ALL + "] " +
            PADDED_TEST_COLOR +
            "[" + dev.BLUE + dev.BRIGHT +
            "some_module" +
            dev.RESET_ALL + "] " +
            dev.CYAN + "foo" + dev.RESET_ALL + "=" + dev.MAGENTA + "'bar'" +
            dev.RESET_ALL + " " +
            dev.CYAN + "key" + dev.RESET_ALL + "=" + dev.MAGENTA + "'value'" +
            dev.RESET_ALL +
            "\n" + stack + "\n\n" + "=" * 79 + "\n" +
            "\n" + exc
        ) == rv

    def test_everything__no_color(self, cr_nc):
        """
        Put all cases together.
        """
        exc = "Traceback:\nFake traceback...\nFakeError: yolo"
        stack = "fake stack trace"

        rv = cr_nc(None, None, {
            "event": "test",
            "exception": exc,
            "key": "value",
            "foo": "bar",
            "timestamp": "13:13",
            "logger": "some_module",
            "level": "error",
            "stack": stack,
        })

        assert (
            "13:13 [" +
            dev._pad("error", cr_nc._longest_level) +
            "] " +
            PADDED_TEST_NO_COLOR +
            "[some_module] " +
            "foo='bar' key='value'" +
            "\n" + stack + "\n\n" + "=" * 79 + "\n" +
            "\n" + exc
        ) == rv
