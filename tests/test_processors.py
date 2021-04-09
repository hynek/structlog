# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.


import datetime
import json
import pickle
import sys

import pytest

from freezegun import freeze_time

import structlog

from structlog.processors import (
    ExceptionPrettyPrinter,
    JSONRenderer,
    KeyValueRenderer,
    StackInfoRenderer,
    TimeStamper,
    UnicodeDecoder,
    UnicodeEncoder,
    _figure_out_exc_info,
    _json_fallback_handler,
    format_exc_info,
)
from structlog.threadlocal import wrap_dict


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
        s = json.dumps(
            wrap_dict(dict)({"a": 42}), default=_json_fallback_handler
        )

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
        with pytest.raises(ValueError) as e:
            TimeStamper(utc=False)

        assert "UNIX timestamps are always UTC." == e.value.args[0]

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


class TestFormatExcInfo:
    def test_formats_tuple(self, monkeypatch):
        """
        If exc_info is a tuple, it is used.
        """
        monkeypatch.setattr(
            structlog.processors,
            "_format_exception",
            lambda exc_info: exc_info,
        )
        d = format_exc_info(None, None, {"exc_info": (None, None, 42)})

        assert {"exception": (None, None, 42)} == d

    def test_gets_exc_info_on_bool(self):
        """
        If exc_info is True, it is obtained using sys.exc_info().
        """
        # monkeypatching sys.exc_info makes currently py.test return 1 on
        # success.
        try:
            raise ValueError("test")
        except ValueError:
            d = format_exc_info(None, None, {"exc_info": True})

        assert "exc_info" not in d
        assert 'raise ValueError("test")\nValueError: test' in d["exception"]

    def test_exception_on_py3(self, monkeypatch):
        """
        Passing exceptions as exc_info is valid on Python 3.
        """
        monkeypatch.setattr(
            structlog.processors,
            "_format_exception",
            lambda exc_info: exc_info,
        )
        try:
            raise ValueError("test")
        except ValueError as e:
            d = format_exc_info(None, None, {"exc_info": e})

            assert {"exception": (ValueError, e, e.__traceback__)} == d
        else:
            pytest.fail("Exception not raised.")

    def test_exception_without_traceback(self):
        """
        If an Exception is missing a traceback, render it anyway.
        """
        rv = format_exc_info(
            None, None, {"exc_info": Exception("no traceback!")}
        )

        assert {"exception": "Exception: no traceback!"} == rv


class TestUnicodeEncoder:
    def test_encodes(self):
        """
        Unicode strings get encoded (as UTF-8 by default).
        """
        ue = UnicodeEncoder()

        assert {"foo": b"b\xc3\xa4r"} == ue(None, None, {"foo": "b\xe4r"})

    def test_passes_arguments(self):
        """
        Encoding options are passed into the encoding call.
        """
        ue = UnicodeEncoder("latin1", "xmlcharrefreplace")

        assert {"foo": b"&#8211;"} == ue(None, None, {"foo": "\u2013"})

    def test_bytes_nop(self):
        """
        If the string is already bytes, don't do anything.
        """
        ue = UnicodeEncoder()

        assert {"foo": b"b\xc3\xa4r"} == ue(None, None, {"foo": b"b\xc3\xa4r"})


class TestUnicodeDecoder:
    def test_decodes(self):
        """
        Byte strings get decoded (as UTF-8 by default).
        """
        ud = UnicodeDecoder()

        assert {"foo": "b\xe4r"} == ud(None, None, {"foo": b"b\xc3\xa4r"})

    def test_passes_arguments(self):
        """
        Encoding options are passed into the encoding call.
        """
        ud = UnicodeDecoder("utf-8", "ignore")

        assert {"foo": ""} == ud(None, None, {"foo": b"\xa1\xa4"})

    def test_bytes_nop(self):
        """
        If the value is already unicode, don't do anything.
        """
        ud = UnicodeDecoder()

        assert {"foo": "b\u2013r"} == ud(None, None, {"foo": "b\u2013r"})


class TestExceptionPrettyPrinter:
    def test_stdout_by_default(self):
        """
        If no file is supplied, use stdout.
        """
        epp = ExceptionPrettyPrinter()

        assert sys.stdout is epp._file

    def test_prints_exception(self, sio):
        """
        If there's an `exception` key in the event_dict, just print it out.
        This happens if `format_exc_info` was run before us in the chain.
        """
        epp = ExceptionPrettyPrinter(file=sio)
        try:
            raise ValueError
        except ValueError:
            ed = format_exc_info(None, None, {"exc_info": True})
        epp(None, None, ed)

        out = sio.getvalue()

        assert "test_prints_exception" in out
        assert "raise ValueError" in out

    def test_removes_exception_after_printing(self, sio):
        """
        After pretty printing `exception` is removed from the event_dict.
        """
        epp = ExceptionPrettyPrinter(sio)
        try:
            raise ValueError
        except ValueError:
            ed = format_exc_info(None, None, {"exc_info": True})

        assert "exception" in ed

        new_ed = epp(None, None, ed)

        assert "exception" not in new_ed

    def test_handles_exc_info(self, sio):
        """
        If `exc_info` is passed in, it behaves like `format_exc_info`.
        """
        epp = ExceptionPrettyPrinter(sio)
        try:
            raise ValueError
        except ValueError:
            epp(None, None, {"exc_info": True})

        out = sio.getvalue()

        assert "test_handles_exc_info" in out
        assert "raise ValueError" in out

    def test_removes_exc_info_after_printing(self, sio):
        """
        After pretty printing `exception` is removed from the event_dict.
        """
        epp = ExceptionPrettyPrinter(sio)
        try:
            raise ValueError
        except ValueError:
            ed = epp(None, None, {"exc_info": True})

        assert "exc_info" not in ed

    def test_nop_if_no_exception(self, sio):
        """
        If there is no exception, don't print anything.
        """
        epp = ExceptionPrettyPrinter(sio)
        epp(None, None, {})

        assert "" == sio.getvalue()

    def test_own_exc_info(self, sio):
        """
        If exc_info is a tuple, use it.
        """
        epp = ExceptionPrettyPrinter(sio)
        try:
            raise ValueError("XXX")
        except ValueError:
            ei = sys.exc_info()

        epp(None, None, {"exc_info": ei})

        assert "XXX" in sio.getvalue()

    def test_exception_on_py3(self, sio):
        """
        On Python 3, it's also legal to pass an Exception.
        """
        epp = ExceptionPrettyPrinter(sio)
        try:
            raise ValueError("XXX")
        except ValueError as e:
            epp(None, None, {"exc_info": e})

        assert "XXX" in sio.getvalue()


@pytest.fixture
def sir():
    return StackInfoRenderer()


class TestStackInfoRenderer:
    def test_removes_stack_info(self, sir):
        """
        The `stack_info` key is removed from `event_dict`.
        """
        ed = sir(None, None, {"stack_info": True})

        assert "stack_info" not in ed

    def test_adds_stack_if_asked(self, sir):
        """
        If `stack_info` is true, `stack` is added.
        """
        ed = sir(None, None, {"stack_info": True})

        assert "stack" in ed

    def test_renders_correct_stack(self, sir):
        ed = sir(None, None, {"stack_info": True})

        assert 'ed = sir(None, None, {"stack_info": True})' in ed["stack"]


class TestFigureOutExcInfo:
    @pytest.mark.parametrize("true_value", [True, 1, 1.1])
    def test_obtains_exc_info_on_True(self, true_value):
        """
        If the passed argument evaluates to True obtain exc_info ourselves.
        """
        try:
            0 / 0
        except Exception:
            assert sys.exc_info() == _figure_out_exc_info(true_value)
        else:
            pytest.fail("Exception not raised.")

    def test_py3_exception_no_traceback(self):
        """
        Exceptions without tracebacks are simply returned with None for
        traceback.
        """
        e = ValueError()

        assert (e.__class__, e, None) == _figure_out_exc_info(e)
