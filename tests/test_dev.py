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
def cr():
    return dev.ConsoleRenderer()


if dev.colorama is not None:
    PADDED_TEST = (
        dev.BRIGHT +
        dev._pad("test", dev._EVENT_WIDTH) +
        dev.RESET_ALL + " "
    )


@pytest.mark.skipif(dev.colorama is None, reason="Requires colorama.")
class TestConsoleRenderer(object):
    def test_plain(self, cr):
        """
        Works with a plain event_dict with only the event.
        """
        rv = cr(None, None, {"event": "test"})

        assert PADDED_TEST == rv

    def test_timestamp(self, cr):
        """
        Timestamps get prepended dimmed..
        """
        rv = cr(None, None, {"event": "test", "timestamp": 42})

        assert (
            dev.DIM + "42" + dev.RESET_ALL +
            " " + PADDED_TEST
        ) == rv

    def test_level(self, cr):
        """
        Levels are rendered aligned, in square brackets, and color coded.
        """
        rv = cr(None, None, {"event": "test", "level": "critical"})

        assert (
            "[" + dev.RED + dev.BRIGHT +
            dev._pad("critical", cr._longest_level) +
            dev.RESET_ALL + "] " +
            PADDED_TEST
        ) == rv

    def test_logger_name(self, cr):
        """
        Logger names are appended after the event.
        """
        rv = cr(None, None, {"event": "test", "logger": "some_module"})

        assert (
            PADDED_TEST +
            "[" + dev.BLUE + dev.BRIGHT +
            "some_module" +
            dev.RESET_ALL + "] "
        ) == rv

    def test_key_values(self, cr):
        """
        Key-value pairs go sorted alphabetically to the end.
        """
        rv = cr(None, None, {
            "event": "test",
            "key": "value",
            "foo": "bar",
        })
        assert (
            PADDED_TEST +
            dev.CYAN + "foo" + dev.RESET_ALL + "=" + dev.MAGENTA + "'bar'" +
            dev.RESET_ALL + " " +
            dev.CYAN + "key" + dev.RESET_ALL + "=" + dev.MAGENTA + "'value'" +
            dev.RESET_ALL
        ) == rv

    def test_exception(self, cr):
        """
        Exceptions are rendered after a new line.
        """
        exc = "Traceback:\nFake traceback...\nFakeError: yolo"

        rv = cr(None, None, {
            "event": "test",
            "exception": exc
        })

        assert (
            PADDED_TEST + "\n" + exc
        ) == rv

    def test_stack_info(self, cr):
        """
        Stack traces are rendered after a new line.
        """
        stack = "fake stack"
        rv = cr(None, None, {
            "event": "test",
            "stack": stack
        })

        assert (
            PADDED_TEST + "\n" + stack
        ) == rv

    def test_pad_event_param(self):
        """
        `pad_event` parameter works.
        """
        rv = dev.ConsoleRenderer(42)(None, None, {"event": "test"})

        assert (
            dev.BRIGHT +
            dev._pad("test", 42) +
            dev.RESET_ALL + " "
        ) == rv

    def test_everything(self, cr):
        """
        Put all cases together.
        """
        exc = "Traceback:\nFake traceback...\nFakeError: yolo"
        stack = "fake stack trace"

        rv = cr(None, None, {
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
            dev._pad("error", cr._longest_level) +
            dev.RESET_ALL + "] " +
            PADDED_TEST +
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
