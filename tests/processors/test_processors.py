# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import annotations

import functools
import inspect
import itertools
import json
import logging
import os
import pickle
import sys
import threading

from io import StringIO

import pytest

import structlog

from structlog import BoundLogger
from structlog._utils import get_processname
from structlog.processors import (
    CallsiteParameter,
    CallsiteParameterAdder,
    EventRenamer,
    ExceptionPrettyPrinter,
    JSONRenderer,
    StackInfoRenderer,
    UnicodeDecoder,
    UnicodeEncoder,
    _figure_out_exc_info,
    format_exc_info,
)
from structlog.stdlib import ProcessorFormatter
from structlog.typing import EventDict

from ..additional_frame import additional_frame


try:
    import simplejson
except ImportError:
    simplejson = None


class TestUnicodeEncoder:
    def test_encodes(self):
        """
        Unicode strings get encoded (as UTF-8 by default).
        """
        e = UnicodeEncoder()

        assert {"foo": b"b\xc3\xa4r"} == e(None, None, {"foo": "b\xe4r"})

    def test_passes_arguments(self):
        """
        Encoding options are passed into the encoding call.
        """
        e = UnicodeEncoder("latin1", "xmlcharrefreplace")

        assert {"foo": b"&#8211;"} == e(None, None, {"foo": "\u2013"})

    def test_bytes_nop(self):
        """
        If the string is already bytes, don't do anything.
        """
        e = UnicodeEncoder()

        assert {"foo": b"b\xc3\xa4r"} == e(None, None, {"foo": b"b\xc3\xa4r"})


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


@pytest.fixture()
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
        """
        The rendered stack is correct.
        """
        ed = sir(None, None, {"stack_info": True})

        assert 'ed = sir(None, None, {"stack_info": True})' in ed["stack"]

    def test_additional_ignores(self):
        """
        Filtering of names works.
        """
        sir = StackInfoRenderer(["tests.additional_frame"])

        ed = additional_frame(
            functools.partial(sir, None, None, {"stack_info": True})
        )

        assert "additional_frame.py" not in ed["stack"]


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


class TestCallsiteParameterAdder:
    parameter_strings = {
        "pathname",
        "filename",
        "module",
        "func_name",
        "lineno",
        "thread",
        "thread_name",
        "process",
        "process_name",
    }

    _all_parameters = set(CallsiteParameter)

    def test_all_parameters(self) -> None:
        """
        All callsite parameters are included in ``self.parameter_strings`` and
        the dictionary returned by ``self.get_callsite_parameters`` contains
        keys for all callsite parameters.
        """

        assert self.parameter_strings == {
            member.value for member in self._all_parameters
        }
        assert self.parameter_strings == self.get_callsite_parameters().keys()

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        ("wrapper_class", "method_name"),
        [
            (structlog.stdlib.BoundLogger, "ainfo"),
            (structlog.stdlib.AsyncBoundLogger, "info"),
        ],
    )
    async def test_async(self, wrapper_class, method_name) -> None:
        """
        Callsite information for async invocations are correct.
        """
        string_io = StringIO()

        class StringIOLogger(structlog.PrintLogger):
            def __init__(self):
                super().__init__(file=string_io)

        processor = self.make_processor(None, ["concurrent", "threading"])
        structlog.configure(
            processors=[processor, JSONRenderer()],
            logger_factory=StringIOLogger,
            wrapper_class=wrapper_class,
            cache_logger_on_first_use=True,
        )

        logger = structlog.stdlib.get_logger()

        callsite_params = self.get_callsite_parameters()
        await getattr(logger, method_name)("baz")
        logger_params = json.loads(string_io.getvalue())

        # These are different when running under async
        for key in ["thread", "thread_name"]:
            callsite_params.pop(key)
            logger_params.pop(key)

        assert {"event": "baz", **callsite_params} == logger_params

    def test_additional_ignores(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Stack frames from modules with names that start with values in
        `additional_ignores` are ignored when determining the callsite.
        """
        test_message = "test message"
        additional_ignores = ["tests.additional_frame"]
        processor = self.make_processor(None, additional_ignores)
        event_dict: EventDict = {"event": test_message}

        # Warning: the next two lines must appear exactly like this to make
        # line numbers match.
        callsite_params = self.get_callsite_parameters(1)
        actual = processor(None, None, event_dict)

        expected = {"event": test_message, **callsite_params}

        assert expected == actual

    @pytest.mark.parametrize(
        ("origin", "parameter_strings"),
        itertools.product(
            ["logging", "structlog"],
            [
                None,
                *[{parameter} for parameter in parameter_strings],
                set(),
                parameter_strings,
                {"pathname", "filename"},
                {"module", "func_name"},
            ],
        ),
    )
    def test_processor(
        self,
        origin: str,
        parameter_strings: set[str] | None,
    ):
        """
        The correct callsite parameters are added to event dictionaries.
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
                callsite_params["func_name"],
            )
            event_dict: EventDict = {
                "event": test_message,
                "_record": record,
                "_from_structlog": False,
            }
            actual = processor(None, None, event_dict)
        else:
            pytest.fail(f"invalid origin {origin}")
        actual = {
            key: value
            for key, value in actual.items()
            if not key.startswith("_")
        }
        callsite_params = self.filter_parameter_dict(
            callsite_params, parameter_strings
        )
        expected = {"event": test_message, **callsite_params}

        assert expected == actual

    @pytest.mark.parametrize(
        ("setup", "origin", "parameter_strings"),
        itertools.product(
            ["common-without-pre", "common-with-pre", "shared", "everywhere"],
            ["logging", "structlog"],
            [
                None,
                *[{parameter} for parameter in parameter_strings],
                set(),
                parameter_strings,
                {"pathname", "filename"},
                {"module", "func_name"},
            ],
        ),
    )
    def test_e2e(
        self,
        setup: str,
        origin: str,
        parameter_strings: set[str] | None,
    ) -> None:
        """
        Logging output contains the correct callsite parameters.
        """
        logger = logging.Logger(sys._getframe().f_code.co_name)
        string_io = StringIO()
        handler = logging.StreamHandler(string_io)
        processors = [self.make_processor(parameter_strings)]
        if setup == "common-without-pre":
            common_processors = processors
            formatter = ProcessorFormatter(
                processors=[*processors, JSONRenderer()]
            )
        elif setup == "common-with-pre":
            common_processors = processors
            formatter = ProcessorFormatter(
                foreign_pre_chain=processors,
                processors=[JSONRenderer()],
            )
        elif setup == "shared":
            common_processors = []
            formatter = ProcessorFormatter(
                processors=[*processors, JSONRenderer()],
            )
        elif setup == "everywhere":
            common_processors = processors
            formatter = ProcessorFormatter(
                foreign_pre_chain=processors,
                processors=[*processors, JSONRenderer()],
            )
        else:
            pytest.fail(f"invalid setup {setup}")
        handler.setFormatter(formatter)
        handler.setLevel(0)
        logger.addHandler(handler)
        logger.setLevel(0)

        test_message = "test message"
        if origin == "logging":
            callsite_params = self.get_callsite_parameters()
            logger.info(test_message)
        elif origin == "structlog":
            ctx = {}
            bound_logger = BoundLogger(
                logger,
                [*common_processors, ProcessorFormatter.wrap_for_formatter],
                ctx,
            )
            callsite_params = self.get_callsite_parameters()
            bound_logger.info(test_message)
        else:
            pytest.fail(f"invalid origin {origin}")

        callsite_params = self.filter_parameter_dict(
            callsite_params, parameter_strings
        )
        actual = {
            key: value
            for key, value in json.loads(string_io.getvalue()).items()
            if not key.startswith("_")
        }
        expected = {"event": test_message, **callsite_params}

        assert expected == actual

    def test_pickeable_callsite_parameter_adder(self) -> None:
        """
        An instance of ``CallsiteParameterAdder`` can be pickled.  This
        functionality may be used to propagate structlog configurations to
        subprocesses.
        """
        pickle.dumps(CallsiteParameterAdder())

    @classmethod
    def make_processor(
        cls,
        parameter_strings: set[str] | None,
        additional_ignores: list[str] | None = None,
    ) -> CallsiteParameterAdder:
        """
        Creates a ``CallsiteParameterAdder`` with parameters matching the
        supplied *parameter_strings* values and with the supplied
        *additional_ignores* values.

        Args:
            parameter_strings:
                Strings for which corresponding ``CallsiteParameters`` should
                be included in the resulting ``CallsiteParameterAdded``.

            additional_ignores:
                Used as *additional_ignores* for the resulting
                ``CallsiteParameterAdded``.
        """
        if parameter_strings is None:
            return CallsiteParameterAdder(
                additional_ignores=additional_ignores
            )

        parameters = cls.filter_parameters(parameter_strings)
        return CallsiteParameterAdder(
            parameters=parameters,
            additional_ignores=additional_ignores,
        )

    @classmethod
    def filter_parameters(
        cls, parameter_strings: set[str] | None
    ) -> set[CallsiteParameter]:
        """
        Returns a set containing all ``CallsiteParameter`` members with values
        that are in ``parameter_strings``.

        Args:
            parameter_strings:
                The parameters strings for which corresponding
                ``CallsiteParameter`` members should be returned. If this value
                is `None` then all ``CallsiteParameter`` will be returned.
        """
        if parameter_strings is None:
            return cls._all_parameters
        return {
            parameter
            for parameter in cls._all_parameters
            if parameter.value in parameter_strings
        }

    @classmethod
    def filter_parameter_dict(
        cls, input: dict[str, object], parameter_strings: set[str] | None
    ) -> dict[str, object]:
        """
        Returns a dictionary that is equivalent to *input* but with all keys
        not in *parameter_strings* removed.

        Args:
            parameter_strings:
                The keys to keep in the dictionary, if this value is ``None``
                then all keys matching ``cls.parameter_strings`` are kept.
        """
        if parameter_strings is None:
            parameter_strings = cls.parameter_strings
        return {
            key: value
            for key, value in input.items()
            if key in parameter_strings
        }

    @classmethod
    def get_callsite_parameters(cls, offset: int = 1) -> dict[str, object]:
        """
        This function creates dictionary of callsite parameters for the line
        that is ``offset`` lines after the invocation of this function.

        Args:
            offset:
                The amount of lines after the invocation of this function that
                callsite parameters should be generated for.
        """
        frame_info = inspect.stack()[1]
        frame_traceback = inspect.getframeinfo(frame_info[0])
        return {
            "pathname": frame_traceback.filename,
            "filename": os.path.basename(frame_traceback.filename),
            "module": os.path.splitext(
                os.path.basename(frame_traceback.filename)
            )[0],
            "func_name": frame_info.function,
            "lineno": frame_info.lineno + offset,
            "thread": threading.get_ident(),
            "thread_name": threading.current_thread().name,
            "process": os.getpid(),
            "process_name": get_processname(),
        }


class TestRenameKey:
    def test_rename_once(self):
        """
        Renaming event to something else works.
        """
        assert {"msg": "hi", "foo": "bar"} == EventRenamer("msg")(
            None, None, {"event": "hi", "foo": "bar"}
        )

    def test_rename_twice(self):
        """
        Renaming both from and to `event` works.
        """
        assert {
            "msg": "hi",
            "event": "fabulous",
            "foo": "bar",
        } == EventRenamer("msg", "_event")(
            None, None, {"event": "hi", "foo": "bar", "_event": "fabulous"}
        )

    def test_replace_by_key_is_optional(self):
        """
        The key that is renamed to `event` doesn't have to exist.
        """
        assert {"msg": "hi", "foo": "bar"} == EventRenamer("msg", "missing")(
            None, None, {"event": "hi", "foo": "bar"}
        )
