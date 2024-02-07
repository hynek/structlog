# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import annotations

import datetime
import json
import pickle

import pytest

from freezegun import freeze_time

from structlog.processors import (
    ExceptionRenderer,
    JSONRenderer,
    KeyValueRenderer,
    LogfmtRenderer,
    MaybeTimeStamper,
    TimeStamper,
    _json_fallback_handler,
    format_exc_info,
)
from structlog.threadlocal import wrap_dict

from ..utils import CustomError


try:
    import simplejson
except ImportError:
    simplejson = None


class TestKeyValueRenderer:
    def test_sort_keys(self, event_dict):
        """
        Keys are sorted if sort_keys is set.
        """
        rv = KeyValueRenderer(sort_keys=True)(None, None, event_dict)

        assert r"a=<A(\o/)> b=[3, 4] x=7 y='test' z=(1, 2)" == rv

    def test_order_complete(self, event_dict):
        """
        Orders keys according to key_order.
        """
        rv = KeyValueRenderer(key_order=["y", "b", "a", "z", "x"])(
            None, None, event_dict
        )

        assert r"y='test' b=[3, 4] a=<A(\o/)> z=(1, 2) x=7" == rv

    def test_order_missing(self, event_dict):
        """
        Missing keys get rendered as None.
        """
        rv = KeyValueRenderer(key_order=["c", "y", "b", "a", "z", "x"])(
            None, None, event_dict
        )

        assert r"c=None y='test' b=[3, 4] a=<A(\o/)> z=(1, 2) x=7" == rv

    def test_order_missing_dropped(self, event_dict):
        """
        Missing keys get dropped
        """
        rv = KeyValueRenderer(
            key_order=["c", "y", "b", "a", "z", "x"], drop_missing=True
        )(None, None, event_dict)

        assert r"y='test' b=[3, 4] a=<A(\o/)> z=(1, 2) x=7" == rv

    def test_order_extra(self, event_dict):
        """
        Extra keys get sorted if sort_keys=True.
        """
        event_dict["B"] = "B"
        event_dict["A"] = "A"

        rv = KeyValueRenderer(
            key_order=["c", "y", "b", "a", "z", "x"], sort_keys=True
        )(None, None, event_dict)

        assert (
            r"c=None y='test' b=[3, 4] a=<A(\o/)> z=(1, 2) x=7 A='A' B='B'"
        ) == rv

    def test_order_sorted_missing_dropped(self, event_dict):
        """
        Keys get sorted if sort_keys=True and extras get dropped.
        """
        event_dict["B"] = "B"
        event_dict["A"] = "A"

        rv = KeyValueRenderer(
            key_order=["c", "y", "b", "a", "z", "x"],
            sort_keys=True,
            drop_missing=True,
        )(None, None, event_dict)

        assert r"y='test' b=[3, 4] a=<A(\o/)> z=(1, 2) x=7 A='A' B='B'" == rv

    def test_random_order(self, event_dict):
        """
        No special ordering doesn't blow up.
        """
        rv = KeyValueRenderer()(None, None, event_dict)

        assert isinstance(rv, str)

    @pytest.mark.parametrize("rns", [True, False])
    def test_repr_native_str(self, rns):
        """
        repr_native_str=False doesn't repr on native strings.
        """
        rv = KeyValueRenderer(repr_native_str=rns)(
            None, None, {"event": "哈", "key": 42, "key2": "哈"}
        )

        cnt = rv.count("哈")
        assert 2 == cnt


class TestLogfmtRenderer:
    def test_sort_keys(self, event_dict):
        """
        Keys are sorted if sort_keys is set.
        """
        rv = LogfmtRenderer(sort_keys=True)(None, None, event_dict)

        assert r'a=<A(\o/)> b="[3, 4]" x=7 y=test z="(1, 2)"' == rv

    def test_order_complete(self, event_dict):
        """
        Orders keys according to key_order.
        """
        rv = LogfmtRenderer(key_order=["y", "b", "a", "z", "x"])(
            None, None, event_dict
        )

        assert r'y=test b="[3, 4]" a=<A(\o/)> z="(1, 2)" x=7' == rv

    def test_order_missing(self, event_dict):
        """
        Missing keys get rendered as None.
        """
        rv = LogfmtRenderer(key_order=["c", "y", "b", "a", "z", "x"])(
            None, None, event_dict
        )

        assert r'c= y=test b="[3, 4]" a=<A(\o/)> z="(1, 2)" x=7' == rv

    def test_order_missing_dropped(self, event_dict):
        """
        Missing keys get dropped
        """
        rv = LogfmtRenderer(
            key_order=["c", "y", "b", "a", "z", "x"], drop_missing=True
        )(None, None, event_dict)

        assert r'y=test b="[3, 4]" a=<A(\o/)> z="(1, 2)" x=7' == rv

    def test_order_extra(self, event_dict):
        """
        Extra keys get sorted if sort_keys=True.
        """
        event_dict["B"] = "B"
        event_dict["A"] = "A"

        rv = LogfmtRenderer(
            key_order=["c", "y", "b", "a", "z", "x"], sort_keys=True
        )(None, None, event_dict)

        assert (
            r'c= y=test b="[3, 4]" a=<A(\o/)> z="(1, 2)" x=7 A=A B=B'
        ) == rv

    def test_order_sorted_missing_dropped(self, event_dict):
        """
        Keys get sorted if sort_keys=True and extras get dropped.
        """
        event_dict["B"] = "B"
        event_dict["A"] = "A"

        rv = LogfmtRenderer(
            key_order=["c", "y", "b", "a", "z", "x"],
            sort_keys=True,
            drop_missing=True,
        )(None, None, event_dict)

        assert r'y=test b="[3, 4]" a=<A(\o/)> z="(1, 2)" x=7 A=A B=B' == rv

    def test_random_order(self, event_dict):
        """
        No special ordering doesn't blow up.
        """
        rv = LogfmtRenderer()(None, None, event_dict)

        assert isinstance(rv, str)

    def test_empty_event_dict(self):
        """
        Empty event dict renders as empty string.
        """
        rv = LogfmtRenderer()(None, None, {})

        assert "" == rv

    def test_bool_as_flag(self):
        """
        If activated, render ``{"a": True}`` as ``a`` instead of ``a=true``.
        """
        event_dict = {"a": True, "b": False}

        rv_abbrev = LogfmtRenderer(bool_as_flag=True)(None, None, event_dict)
        assert r"a b=false" == rv_abbrev

        rv_no_abbrev = LogfmtRenderer(bool_as_flag=False)(
            None, None, event_dict
        )
        assert r"a=true b=false" == rv_no_abbrev

    def test_reference_format(self):
        """
        Test rendering according to example at
        https://pkg.go.dev/github.com/kr/logfmt
        """
        event_dict = {
            "foo": "bar",
            "a": 14,
            "baz": "hello kitty",
            "cool%story": "bro",
            "f": True,
            "%^asdf": True,
        }

        rv = LogfmtRenderer()(None, None, event_dict)
        assert 'foo=bar a=14 baz="hello kitty" cool%story=bro f %^asdf' == rv

    def test_equal_sign_or_space_in_value(self):
        """
        Values with equal signs are always quoted.
        """
        event_dict = {
            "without": "somevalue",
            "withequal": "some=value",
            "withspace": "some value",
        }

        rv = LogfmtRenderer()(None, None, event_dict)
        assert (
            r'without=somevalue withequal="some=value" withspace="some value"'
            == rv
        )

    def test_invalid_key(self):
        """
        Keys cannot contain space characters.
        """
        event_dict = {"invalid key": "somevalue"}

        with pytest.raises(ValueError, match='Invalid key: "invalid key"'):
            LogfmtRenderer()(None, None, event_dict)

    def test_newline_in_value(self):
        """
        Newlines in values are escaped.
        """
        event_dict = {"with_newline": "some\nvalue"}

        rv = LogfmtRenderer()(None, None, event_dict)

        assert r"with_newline=some\nvalue" == rv

    @pytest.mark.parametrize(
        ("raw", "escaped"),
        [
            # Slash by itself does not need to be escaped.
            (r"a\slash", r"a\slash"),
            # A quote requires quoting, and escaping the quote.
            ('a"quote', r'"a\"quote"'),
            # If anything triggers quoting of the string, then the slash must
            # be escaped.
            (
                r'a\slash with space or a"quote',
                r'"a\\slash with space or a\"quote"',
            ),
            (
                r"I want to render this \"string\" with logfmtrenderer",
                r'"I want to render this \\\"string\\\" with logfmtrenderer"',
            ),
        ],
    )
    def test_escaping(self, raw, escaped):
        """
        Backslashes and quotes are escaped.
        """
        rv = LogfmtRenderer()(None, None, {"key": raw})

        assert f"key={escaped}" == rv


class TestJSONRenderer:
    def test_renders_json(self, event_dict):
        """
        Renders a predictable JSON string.
        """
        rv = JSONRenderer(sort_keys=True)(None, None, event_dict)

        assert (
            r'{"a": "<A(\\o/)>", "b": [3, 4], "x": 7, '
            r'"y": "test", "z": '
            r"[1, 2]}"
        ) == rv

    def test_FallbackEncoder_handles_ThreadLocalDictWrapped_dicts(self):
        """
        Our fallback handling handles properly ThreadLocalDictWrapper values.
        """
        with pytest.deprecated_call():
            d = wrap_dict(dict)

        s = json.dumps(d({"a": 42}), default=_json_fallback_handler)

        assert '{"a": 42}' == s

    def test_FallbackEncoder_falls_back(self):
        """
        The fallback handler uses repr if it doesn't know the type.
        """
        s = json.dumps(
            {"date": datetime.date(1980, 3, 25)},
            default=_json_fallback_handler,
        )

        assert '{"date": "datetime.date(1980, 3, 25)"}' == s

    def test_serializer(self):
        """
        A custom serializer is used if specified.
        """
        jr = JSONRenderer(serializer=lambda obj, **kw: {"a": 42})
        obj = object()

        assert {"a": 42} == jr(None, None, obj)

    def test_custom_fallback(self):
        """
        A custom fallback handler can be used.
        """
        jr = JSONRenderer(default=lambda x: repr(x)[::-1])
        d = {"date": datetime.date(1980, 3, 25)}

        assert '{"date": ")52 ,3 ,0891(etad.emitetad"}' == jr(None, None, d)

    @pytest.mark.skipif(simplejson is None, reason="simplejson is missing.")
    def test_simplejson(self, event_dict):
        """
        Integration test with simplejson.
        """
        jr = JSONRenderer(serializer=simplejson.dumps)

        assert {
            "a": "<A(\\o/)>",
            "b": [3, 4],
            "x": 7,
            "y": "test",
            "z": [1, 2],
        } == json.loads(jr(None, None, event_dict))


class TestTimeStamper:
    def test_disallows_non_utc_unix_timestamps(self):
        """
        A asking for a UNIX timestamp with a timezone that's not UTC raises a
        ValueError.
        """
        with pytest.raises(
            ValueError, match="UNIX timestamps are always UTC."
        ):
            TimeStamper(utc=False)

    def test_inserts_utc_unix_timestamp_by_default(self):
        """
        Per default a float UNIX timestamp is used.
        """
        ts = TimeStamper()
        d = ts(None, None, {})

        # freezegun doesn't work with time.time. :(
        assert isinstance(d["timestamp"], float)

    @freeze_time("1980-03-25 16:00:00")
    def test_local(self):
        """
        Timestamp in local timezone work.  We can't add a timezone to the
        string without additional libraries.
        """
        ts = TimeStamper(fmt="iso", utc=False)
        d = ts(None, None, {})

        assert "1980-03-25T16:00:00" == d["timestamp"]

    @freeze_time("1980-03-25 16:00:00")
    def test_formats(self):
        """
        The fmt string is respected.
        """
        ts = TimeStamper(fmt="%Y")
        d = ts(None, None, {})

        assert "1980" == d["timestamp"]

    @freeze_time("1980-03-25 16:00:00")
    def test_adds_Z_to_iso(self):
        """
        stdlib's isoformat is buggy, so we fix it.
        """
        ts = TimeStamper(fmt="iso", utc=True)
        d = ts(None, None, {})

        assert "1980-03-25T16:00:00Z" == d["timestamp"]

    @freeze_time("1980-03-25 16:00:00")
    def test_key_can_be_specified(self):
        """
        Timestamp is stored with the specified key.
        """
        ts = TimeStamper(fmt="%m", key="month")
        d = ts(None, None, {})

        assert "03" == d["month"]

    @freeze_time("1980-03-25 16:00:00")
    @pytest.mark.parametrize("fmt", [None, "%Y"])
    @pytest.mark.parametrize("utc", [True, False])
    @pytest.mark.parametrize("key", [None, "other-key"])
    @pytest.mark.parametrize("proto", range(pickle.HIGHEST_PROTOCOL + 1))
    def test_pickle(self, fmt, utc, key, proto):
        """
        TimeStamper is serializable.
        """
        # UNIX timestamps must be UTC.
        if fmt is None and not utc:
            pytest.skip()

        ts = TimeStamper()

        assert ts(None, None, {}) == pickle.loads(pickle.dumps(ts, proto))(
            None, None, {}
        )

    def test_apply_freezegun_after_instantiation(self):
        """
        Freezing time after instantiation of TimeStamper works.
        """
        ts = TimeStamper(fmt="iso", utc=False)

        with freeze_time("1980-03-25 16:00:00", tz_offset=1):
            d = ts(None, None, {})

            assert "1980-03-25T17:00:00" == d["timestamp"]


class TestMaybeTimeStamper:
    def test_overwrite(self):
        """
        If there is a timestamp, leave it.
        """
        mts = MaybeTimeStamper()

        assert {"timestamp": 42} == mts(None, None, {"timestamp": 42})

    def test_none(self):
        """
        If there is no timestamp, add one.
        """
        mts = MaybeTimeStamper()

        assert "timestamp" in mts(None, None, {})


class TestFormatExcInfo:
    def test_custom_formatter(self):
        """
        The exception formatter can be changed.
        """
        formatter = ExceptionRenderer(lambda _: "There is no exception!")

        try:
            raise CustomError("test")
        except CustomError as e:
            exc = e

        assert formatter(None, None, {"exc_info": exc}) == {
            "exception": "There is no exception!"
        }

    @pytest.mark.parametrize("ei", [False, None, ""])
    def test_nop(self, ei):
        """
        If exc_info is falsey, only remove the key.
        """
        assert {} == ExceptionRenderer()(None, None, {"exc_info": ei})

    def test_nop_missing(self):
        """
        If event dict doesn't contain exc_info, do nothing.
        """
        assert {} == ExceptionRenderer()(None, None, {})

    def test_formats_tuple(self):
        """
        If exc_info is a tuple, it is used.
        """
        formatter = ExceptionRenderer(lambda exc_info: exc_info)
        d = formatter(None, None, {"exc_info": (None, None, 42)})

        assert {"exception": (None, None, 42)} == d

    def test_gets_exc_info_on_bool(self):
        """
        If exc_info is True, it is obtained using sys.exc_info().
        """
        # monkeypatching sys.exc_info makes currently pytest return 1 on
        # success.
        try:
            raise ValueError("test")
        except ValueError:
            d = ExceptionRenderer()(None, None, {"exc_info": True})

        assert "exc_info" not in d
        assert 'raise ValueError("test")' in d["exception"]
        assert "ValueError: test" in d["exception"]

    def test_exception(self):
        """
        Passing exceptions as exc_info is valid.
        """
        formatter = ExceptionRenderer(lambda exc_info: exc_info)

        try:
            raise ValueError("test")
        except ValueError as e:
            exc = e
        else:
            pytest.fail("Exception not raised.")

        assert {
            "exception": (ValueError, exc, exc.__traceback__)
        } == formatter(None, None, {"exc_info": exc})

    def test_exception_without_traceback(self):
        """
        If an Exception is missing a traceback, render it anyway.
        """
        rv = ExceptionRenderer()(
            None, None, {"exc_info": Exception("no traceback!")}
        )

        assert {"exception": "Exception: no traceback!"} == rv

    def test_format_exception(self):
        """
        "format_exception" is the "ExceptionRenderer" with default settings.
        """
        try:
            raise ValueError("test")
        except ValueError as e:
            a = format_exc_info(None, None, {"exc_info": e})
            b = ExceptionRenderer()(None, None, {"exc_info": e})

        assert a == b

    @pytest.mark.parametrize("ei", [True, (None, None, None)])
    def test_no_exception(self, ei):
        """
        A missing exception does not blow up.
        """
        assert {"exception": "MISSING"} == format_exc_info(
            None, None, {"exc_info": ei}
        )
