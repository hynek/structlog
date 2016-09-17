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


@pytest.fixture
def cr():
    return dev.ConsoleRenderer(colors=dev._has_colorama)


@pytest.fixture
def styles(cr):
    return cr._styles


@pytest.fixture
def padded(styles):
    return (
        styles.bright +
        dev._pad("test", dev._EVENT_WIDTH) +
        styles.reset + " "
    )


@pytest.fixture
def unpadded(styles):
    return styles.bright + "test" + styles.reset


class TestConsoleRenderer(object):
    @pytest.mark.skipif(dev._has_colorama, reason="Colorama must be missing.")
    def test_missing_colorama(self):
        """
        ConsoleRenderer(colors=True) raises SystemError on initialization if
        colorama is missing.
        """
        with pytest.raises(SystemError) as e:
            dev.ConsoleRenderer()

        assert (
            "ConsoleRenderer with `colors=True` requires the colorama package "
            "installed."
        ) in e.value.args[0]

    def test_plain(self, cr, styles, unpadded):
        """
        Works with a plain event_dict with only the event.
        """
        rv = cr(None, None, {"event": "test"})

        assert unpadded == rv

    def test_timestamp(self, cr, styles, unpadded):
        """
        Timestamps get prepended.
        """
        rv = cr(None, None, {"event": "test", "timestamp": 42})

        assert (
            styles.timestamp + "42" + styles.reset + " " + unpadded
        ) == rv

    def test_level(self, cr, styles, padded):
        """
        Levels are rendered aligned, in square brackets, and color coded.
        """
        rv = cr(None, None, {
            "event": "test", "level": "critical", "foo": "bar"
        })

        assert (
            "[" + dev.RED + styles.bright +
            dev._pad("critical", cr._longest_level) +
            styles.reset + "] " +
            padded +
            styles.kv_key + "foo" + styles.reset + "=" +
            styles.kv_value + "'bar'" + styles.reset
        ) == rv

    def test_logger_name(self, cr, styles, padded):
        """
        Logger names are appended after the event.
        """
        rv = cr(None, None, {"event": "test", "logger": "some_module"})

        assert (
            padded +
            "[" + dev.BLUE + styles.bright +
            "some_module" +
            styles.reset + "] "
        ) == rv

    def test_key_values(self, cr, styles, padded):
        """
        Key-value pairs go sorted alphabetically to the end.
        """
        rv = cr(None, None, {
            "event": "test",
            "key": "value",
            "foo": "bar",
        })
        assert (
            padded +
            styles.kv_key + "foo" + styles.reset + "=" +
            styles.kv_value + "'bar'" +
            styles.reset + " " +
            styles.kv_key + "key" + styles.reset + "=" +
            styles.kv_value + "'value'" +
            styles.reset
        ) == rv

    def test_exception(self, cr, padded):
        """
        Exceptions are rendered after a new line.
        """
        exc = "Traceback:\nFake traceback...\nFakeError: yolo"

        rv = cr(None, None, {
            "event": "test",
            "exception": exc
        })

        assert (
            padded + "\n" + exc
        ) == rv

    def test_stack_info(self, cr, padded):
        """
        Stack traces are rendered after a new line.
        """
        stack = "fake stack"
        rv = cr(None, None, {
            "event": "test",
            "stack": stack
        })

        assert (
            padded + "\n" + stack
        ) == rv

    def test_pad_event_param(self, styles):
        """
        `pad_event` parameter works.
        """
        rv = dev.ConsoleRenderer(42, dev._has_colorama)(None, None, {
            "event": "test",
            "foo": "bar"
        })

        assert (
            styles.bright +
            dev._pad("test", 42) +
            styles.reset + " " +
            styles.kv_key + "foo" + styles.reset + "=" +
            styles.kv_value + "'bar'" + styles.reset
        ) == rv

    def test_everything(self, cr, styles, padded):
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
            styles.timestamp + "13:13" + styles.reset +
            " [" + styles.level_error + styles.bright +
            dev._pad("error", cr._longest_level) +
            styles.reset + "] " +
            padded +
            "[" + dev.BLUE + styles.bright +
            "some_module" +
            styles.reset + "] " +
            styles.kv_key + "foo" + styles.reset + "=" +
            styles.kv_value + "'bar'" +
            styles.reset + " " +
            styles.kv_key + "key" + styles.reset + "=" +
            styles.kv_value + "'value'" +
            styles.reset +
            "\n" + stack + "\n\n" + "=" * 79 + "\n" +
            "\n" + exc
        ) == rv

    def test_colorama_colors_false(self):
        """
        If colors is False, don't use colors or styles ever.
        """
        plain_cr = dev.ConsoleRenderer(colors=False)

        rv = plain_cr(None, None, {
            "event": "event", "level": "info", "foo": "bar"
        })

        assert dev._PlainStyles is plain_cr._styles
        assert "[info     ] event                          foo='bar'" == rv
