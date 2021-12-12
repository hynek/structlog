# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import datetime
import inspect
import itertools
import json
import logging
import os
import pickle
import sys
import threading

from io import StringIO
from typing import Any, Dict, List, Optional, Set

import pytest

from freezegun import freeze_time

import structlog

from structlog import BoundLogger
from structlog._utils import get_processname
from structlog.processors import (
    CALLSITE_PARAMETERS,
    CallsiteParameter,
    CallsiteParameterAdder,
    ExceptionPrettyPrinter,
    JSONRenderer,
    KeyValueRenderer,
    LogfmtRenderer,
    StackInfoRenderer,
    TimeStamper,
    UnicodeDecoder,
    UnicodeEncoder,
    _figure_out_exc_info,
    _json_fallback_handler,
    format_exc_info,
)
from structlog.stdlib import ProcessorFormatter
from structlog.threadlocal import wrap_dict
from structlog.types import EventDict
from tests.utils import mock_getframe


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
        event_dict = {
            "invalid key": "somevalue",
        }

        with pytest.raises(ValueError) as e:
            LogfmtRenderer()(None, None, event_dict)

        assert 'Invalid key: "invalid key"' == e.value.args[0]


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

    @pytest.mark.parametrize(
        ("utc", "expect"),
        [
            (True, "1980-03-25T16:00:00Z"),
            (False, "1980-03-25T17:00:00"),
        ],
    )
    def test_apply_freezegun_after_instantiation(self, utc, expect):
        """
        Instantiate TimeStamper after mocking datetime
        """
        ts = TimeStamper(fmt="iso", utc=utc)
        with freeze_time("1980-03-25 16:00:00", tz_offset=1):
            d = ts(None, None, {})
            assert expect == d["timestamp"]


class TestFormatExcInfo:
    @pytest.mark.parametrize("ei", [False, None, ""])
    def test_nop(self, ei):
        """
        If exc_info is falsey, only remove the key.
        """
        assert {} == format_exc_info(None, None, {"exc_info": ei})

    def test_nop_missing(self):
        """
        If event dict doesn't contain exc_info, do nothing.
        """
        assert {} == format_exc_info(None, None, {})

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
        # monkeypatching sys.exc_info makes currently pytest return 1 on
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


class TestCallsiteInfoAdder:
    parameter_strings = {
        "pathname",
        "filename",
        "module",
        "funcName",
        "lineno",
        "thread",
        "threadName",
        "process",
        "processName",
    }

    def test_all_parameters(self) -> None:
        assert self.parameter_strings == {
            member.value for member in CALLSITE_PARAMETERS
        }

    def test_additional_ignores(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Test that aditional ignores results in frames from matching module
        names to be ignored.
        """
        test_message = "test message"
        additional_ignores = ["tests.utils"]
        processor = self.make_processor(None, additional_ignores)
        event_dict: EventDict = {"event": test_message}

        # WARNING: The below three lines are sensitive to relative line numbers
        # (i.e. the invocation of processor must be two lines after the
        # invocation of get_callsite_parameters) and is order sensitive (i.e.
        # monkeypatch.setattr must occur after get_callsite_parameters but
        # before invocation of processor).
        callsite_params = self.get_callsite_parameters(2)
        monkeypatch.setattr(sys, "_getframe", value=mock_getframe)
        actual = processor(None, None, event_dict)

        sys.stderr.write(f"actual={actual}\n")
        expected = {
            "event": test_message,
            **callsite_params,
        }
        sys.stderr.write(f"expected={expected}\n")
        assert expected == actual

    @pytest.mark.parametrize(
        "origin, parameter_strings",
        itertools.product(
            ["logging", "structlog"],
            [
                None,
                *[{parameter} for parameter in parameter_strings],
                set(),
                parameter_strings,
                {"pathname", "filename"},
                {"module", "funcName"},
            ],
        ),
    )
    def test_processor(
        self,
        origin: str,
        parameter_strings: Optional[Set[str]],
    ):
        """
        Extra attributes of a LogRecord object are added to the event dict.
        """
        test_message = "test message"
        processor = self.make_processor(parameter_strings)
        if origin == "structlog":
            event_dict: EventDict = {"event": test_message}
            callsite_params = self.get_callsite_parameters()
            actual = processor(None, None, event_dict)
        elif origin == "logging":
            callsite_params = self.get_callsite_parameters()
            record = logging.LogRecord(
                "name",
                logging.INFO,
                callsite_params["pathname"],
                callsite_params["lineno"],
                test_message,
                None,
                None,
                callsite_params["funcName"],
            )
            event_dict: EventDict = {
                "event": test_message,
                "_record": record,
                "_from_structlog": False,
            }
            actual = processor(None, None, event_dict)
        else:
            raise ValueError(f"invalid origin {origin}")
        actual = {
            key: value
            for key, value in actual.items()
            if not key.startswith("_")
        }
        callsite_params = self.filter_parameter_dict(
            callsite_params, parameter_strings
        )
        expected = {
            "event": test_message,
            **callsite_params,
        }
        assert expected == actual

    @pytest.mark.parametrize(
        "setup, origin, parameter_strings",
        itertools.product(
            ["common-without-pre", "common-with-pre", "shared", "everywhere"],
            ["logging", "structlog"],
            [
                None,
                *[{parameter} for parameter in parameter_strings],
                set(),
                parameter_strings,
                {"pathname", "filename"},
                {"module", "funcName"},
            ],
        ),
    )
    def test_e2e(
        self,
        setup: str,
        origin: str,
        parameter_strings: Optional[Set[str]],
    ) -> None:
        logger = logging.Logger(sys._getframe().f_code.co_name)
        string_io = StringIO()
        handler = logging.StreamHandler(string_io)
        if setup == "common-without-pre":
            processors = [self.make_processor(parameter_strings)]
            common_processors = processors
            formatter = ProcessorFormatter(
                processors=[*processors, JSONRenderer()]
            )
        elif setup == "common-with-pre":
            processors = [self.make_processor(parameter_strings)]
            common_processors = processors
            formatter = ProcessorFormatter(
                foreign_pre_chain=processors,
                processors=[JSONRenderer()],
            )
        elif setup == "shared":
            processors = [self.make_processor(parameter_strings)]
            common_processors = []
            formatter = ProcessorFormatter(
                processors=[*processors, JSONRenderer()],
            )
        elif setup == "everywhere":
            processors = [self.make_processor(parameter_strings)]
            common_processors = processors
            formatter = ProcessorFormatter(
                foreign_pre_chain=processors,
                processors=[*processors, JSONRenderer()],
            )
        else:
            raise ValueError(f"invalid setup {setup}")
        handler.setFormatter(formatter)
        handler.setLevel(0)
        logger.addHandler(handler)
        logger.setLevel(0)

        test_message = "test message"
        if origin == "logging":
            callsite_params = self.get_callsite_parameters()
            logger.info(test_message)
        elif origin == "structlog":
            ctx: Dict[str, Any] = {}
            bound_logger = BoundLogger(
                logger,
                [*common_processors, ProcessorFormatter.wrap_for_formatter],
                ctx,
            )
            callsite_params = self.get_callsite_parameters()
            bound_logger.info(test_message)
        else:
            raise ValueError(f"invalid front {origin}")

        callsite_params = self.filter_parameter_dict(
            callsite_params, parameter_strings
        )
        actual = {
            key: value
            for key, value in json.loads(string_io.getvalue()).items()
            if not key.startswith("_")
        }
        expected = {
            "event": test_message,
            **callsite_params,
        }
        assert expected == actual

    @classmethod
    def make_processor(
        cls,
        parameter_strings: Optional[Set[str]],
        additional_ignores: Optional[List[str]] = None,
    ) -> CallsiteParameterAdder:
        """
        Creates a processor with parameters matching the supplied
        ``parameter_strings`` value.
        """
        if parameter_strings is None:
            return CallsiteParameterAdder(
                additional_ignores=additional_ignores
            )
        else:
            parameters = cls.filter_parameters(parameter_strings)
            return CallsiteParameterAdder(
                parameters=parameters,
                additional_ignores=additional_ignores,
            )

    @classmethod
    def filter_parameters(
        cls, parameter_strings: Optional[Set[str]]
    ) -> Set[CallsiteParameter]:
        """
        Returns all `structlog.processor.CALLSITE_PARAMETERS` that match the
        set of `parameter_strings`.

        :param parameter_strings:
            The parameters strings for which correspnding
            `structlog.processor.CALLSITE_PARAMETERS` values should be
            returned. If this value is `None` then all
            `structlog.processor.CALLSITE_PARAMETERS` values will be returned.
        """
        if parameter_strings is None:
            return CALLSITE_PARAMETERS
        return {
            parameter
            for parameter in CALLSITE_PARAMETERS
            if parameter.value in parameter_strings
        }

    @classmethod
    def filter_parameter_dict(
        cls, input: Dict[str, Any], parameter_strings: Optional[Set[str]]
    ) -> Dict[str, Any]:
        """
        Filter a dictionary according to provided parameter strings.

        :param parameter_strings: The parameters to keep in the dictionary, if
            this value is None then all parameter strings are included.
        """
        if parameter_strings is None:
            parameter_strings = cls.parameter_strings
        return {
            key: value
            for key, value in input.items()
            if key in parameter_strings
        }

    @classmethod
    def get_callsite_parameters(cls, offset: int = 1) -> Dict[str, Any]:
        """
        This function creates callsite parameters for the line that is `offset`
        lines after it.

        :param offset: The amount of lines after the invocation of this
            function that callsite parameters should be generated for.
        """
        frame_info = inspect.stack()[1]
        frame_traceback = inspect.getframeinfo(frame_info[0])
        return {
            "pathname": frame_traceback.filename,
            "filename": os.path.basename(frame_traceback.filename),
            "module": os.path.splitext(
                os.path.basename(frame_traceback.filename)
            )[0],
            "funcName": frame_info.function,
            "lineno": frame_info.lineno + offset,
            "thread": threading.get_ident(),
            "threadName": threading.current_thread().name,
            "process": os.getpid(),
            "processName": get_processname(),
        }
