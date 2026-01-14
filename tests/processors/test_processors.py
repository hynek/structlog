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
    SensitiveDataRedactor,
    StackInfoRenderer,
    UnicodeDecoder,
    UnicodeEncoder,
    _figure_out_exc_info,
    format_exc_info,
)
from structlog.stdlib import ProcessorFormatter
from structlog.typing import EventDict, ExcInfo

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

    def test_uses_exception_formatter(self, sio):
        """
        If an `exception_formatter` is passed, use that to render the
        exception rather than the default.
        """

        def formatter(exc_info: ExcInfo) -> str:
            return f"error: {exc_info}"

        epp = ExceptionPrettyPrinter(file=sio, exception_formatter=formatter)
        try:
            raise ValueError
        except ValueError as e:
            epp(None, None, {"exc_info": True})
            formatted = formatter(e)

        out = sio.getvalue()

        assert formatted in out

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

    # Exclude QUAL_NAME from the general set to keep parity with stdlib
    # LogRecord-derived parameters. QUAL_NAME is tested separately.
    _all_parameters = {
        p
        for p in set(CallsiteParameter)
        if p is not CallsiteParameter.QUAL_NAME
    }

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

    @pytest.mark.skipif(
        sys.version_info < (3, 11), reason="QUAL_NAME requires Python 3.11+"
    )
    def test_qual_name_structlog(self) -> None:
        """
        QUAL_NAME is added for structlog-originated events on Python 3.11+.
        """
        processor = CallsiteParameterAdder(
            parameters={CallsiteParameter.QUAL_NAME}
        )
        event_dict: EventDict = {"event": "msg"}
        actual = processor(None, None, event_dict)

        assert actual["qual_name"].endswith(
            f"{self.__class__.__name__}.test_qual_name_structlog"
        )

    def test_qual_name_logging_origin_absent(self) -> None:
        """
        QUAL_NAME is not sourced from stdlib LogRecord and remains absent
        (because it doesn't exist).
        """
        processor = CallsiteParameterAdder(
            parameters={CallsiteParameter.QUAL_NAME}
        )
        record = logging.LogRecord(
            "name",
            logging.INFO,
            __file__,
            0,
            "message",
            None,
            None,
            "func",
        )
        event_dict: EventDict = {
            "event": "message",
            "_record": record,
            "_from_structlog": False,
        }
        actual = processor(None, None, event_dict)

        assert "qual_name" not in actual

    @pytest.mark.asyncio
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
                parameters=cls._all_parameters,
                additional_ignores=additional_ignores,
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


def _test_pickle_redactor(field_name, value, path):
    return "***"


def _test_pickle_audit(field_name, value, path):
    pass


def _extract_extra(logger, log_method, event_dict):
    """
    Extracts extra attributes from LogRecord to event_dict for testing.
    """
    record = event_dict.get("_record")
    if record:
        if hasattr(record, "password"):
            event_dict["password"] = record.password
        if hasattr(record, "api_key"):
            event_dict["api_key"] = record.api_key
        if hasattr(record, "user"):
            event_dict["user"] = record.user
    return event_dict


class TestSensitiveDataRedactor:
    def test_redacts_sensitive_field(self):
        """
        Sensitive fields are replaced with the placeholder.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["password"])

        assert {"user": "alice", "password": "[REDACTED]"} == redactor(
            None, None, {"user": "alice", "password": "s3cr3t"}
        )

    def test_redacts_multiple_sensitive_fields(self):
        """
        Multiple sensitive fields are all redacted.
        """
        redactor = SensitiveDataRedactor(
            sensitive_fields=["password", "api_key", "secret"]
        )

        assert {
            "user": "alice",
            "password": "[REDACTED]",
            "api_key": "[REDACTED]",
            "secret": "[REDACTED]",
        } == redactor(
            None,
            None,
            {
                "user": "alice",
                "password": "s3cr3t",
                "api_key": "abc123",
                "secret": "xyz789",
            },
        )

    def test_custom_placeholder(self):
        """
        A custom placeholder can be specified.
        """
        redactor = SensitiveDataRedactor(
            sensitive_fields=["password"], placeholder="***"
        )

        assert {"password": "***"} == redactor(
            None, None, {"password": "s3cr3t"}
        )

    def test_redacts_nested_dict(self):
        """
        Sensitive fields in nested dictionaries are redacted.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["api_key"])

        assert {
            "config": {"api_key": "[REDACTED]", "timeout": 30}
        } == redactor(
            None, None, {"config": {"api_key": "abc123", "timeout": 30}}
        )

    def test_redacts_deeply_nested_dict(self):
        """
        Sensitive fields in deeply nested dictionaries are redacted.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["secret"])

        assert {
            "level1": {"level2": {"level3": {"secret": "[REDACTED]"}}}
        } == redactor(
            None,
            None,
            {"level1": {"level2": {"level3": {"secret": "deep_secret"}}}},
        )

    def test_redacts_in_list_of_dicts(self):
        """
        Sensitive fields in dictionaries within lists are redacted.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["password"])

        assert {
            "users": [
                {"name": "alice", "password": "[REDACTED]"},
                {"name": "bob", "password": "[REDACTED]"},
            ]
        } == redactor(
            None,
            None,
            {
                "users": [
                    {"name": "alice", "password": "pass1"},
                    {"name": "bob", "password": "pass2"},
                ]
            },
        )

    def test_redacts_nested_lists(self):
        """
        Sensitive fields in nested list structures are redacted.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["token"])

        assert {"data": [[{"token": "[REDACTED]"}]]} == redactor(
            None,
            None,
            {"data": [[{"token": "secret_token"}]]},
        )

    def test_leaves_non_sensitive_fields_unchanged(self):
        """
        Non-sensitive fields are not modified.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["password"])

        assert {
            "user": "alice",
            "email": "alice@example.com",
            "age": 30,
        } == redactor(
            None,
            None,
            {"user": "alice", "email": "alice@example.com", "age": 30},
        )

    def test_empty_sensitive_fields(self):
        """
        When no sensitive fields are specified, nothing is redacted.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=[])

        assert {"password": "s3cr3t"} == redactor(
            None, None, {"password": "s3cr3t"}
        )

    def test_empty_event_dict(self):
        """
        An empty event dict is handled gracefully.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["password"])

        assert {} == redactor(None, None, {})

    def test_redacts_various_value_types(self):
        """
        Sensitive fields with various value types are all redacted.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["secret"])

        assert {"secret": "[REDACTED]"} == redactor(
            None, None, {"secret": "string"}
        )
        assert {"secret": "[REDACTED]"} == redactor(
            None, None, {"secret": 12345}
        )
        assert {"secret": "[REDACTED]"} == redactor(
            None, None, {"secret": ["list", "of", "values"]}
        )
        assert {"secret": "[REDACTED]"} == redactor(
            None, None, {"secret": {"nested": "dict"}}
        )
        assert {"secret": "[REDACTED]"} == redactor(
            None, None, {"secret": None}
        )

    def test_pickleable(self):
        """
        An instance of SensitiveDataRedactor can be pickled.
        """
        redactor = SensitiveDataRedactor(
            sensitive_fields=["password", "api_key"], placeholder="***"
        )
        pickle.dumps(redactor)

    def test_pattern_star_prefix(self):
        """
        Pattern with * prefix matches fields ending with the suffix.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["*_key"])

        assert {
            "api_key": "[REDACTED]",
            "secret_key": "[REDACTED]",
            "user": "alice",
        } == redactor(
            None,
            None,
            {"api_key": "abc123", "secret_key": "xyz789", "user": "alice"},
        )

    def test_pattern_star_suffix(self):
        """
        Pattern with * suffix matches fields starting with the prefix.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["api_*"])

        assert {
            "api_key": "[REDACTED]",
            "api_secret": "[REDACTED]",
            "api_token_v2": "[REDACTED]",
            "user": "alice",
        } == redactor(
            None,
            None,
            {
                "api_key": "abc",
                "api_secret": "xyz",
                "api_token_v2": "123",
                "user": "alice",
            },
        )

    def test_pattern_star_contains(self):
        """
        Pattern with * on both sides matches fields containing the substring.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["*password*"])

        assert {
            "password": "[REDACTED]",
            "user_password": "[REDACTED]",
            "password_hash": "[REDACTED]",
            "old_password_backup": "[REDACTED]",
            "username": "alice",
        } == redactor(
            None,
            None,
            {
                "password": "abc",
                "user_password": "xyz",
                "password_hash": "hash123",
                "old_password_backup": "old",
                "username": "alice",
            },
        )

    def test_pattern_question_mark(self):
        """
        Pattern with ? matches exactly one character.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["key?"])

        assert {
            "key1": "[REDACTED]",
            "key2": "[REDACTED]",
            "keyA": "[REDACTED]",
            "key": "unchanged",
            "key12": "unchanged",
        } == redactor(
            None,
            None,
            {
                "key1": "a",
                "key2": "b",
                "keyA": "c",
                "key": "unchanged",
                "key12": "unchanged",
            },
        )

    def test_multiple_patterns(self):
        """
        Multiple patterns can be used together.
        """
        redactor = SensitiveDataRedactor(
            sensitive_fields=["*password*", "api_*", "*_token"]
        )

        assert {
            "user_password": "[REDACTED]",
            "api_key": "[REDACTED]",
            "auth_token": "[REDACTED]",
            "username": "alice",
        } == redactor(
            None,
            None,
            {
                "user_password": "pass",
                "api_key": "key",
                "auth_token": "token",
                "username": "alice",
            },
        )

    def test_mixed_exact_and_patterns(self):
        """
        Exact matches and patterns can be mixed.
        """
        redactor = SensitiveDataRedactor(
            sensitive_fields=["password", "*_secret", "api_*"]
        )

        assert {
            "password": "[REDACTED]",
            "user_secret": "[REDACTED]",
            "api_key": "[REDACTED]",
            "username": "alice",
        } == redactor(
            None,
            None,
            {
                "password": "pass",
                "user_secret": "secret",
                "api_key": "key",
                "username": "alice",
            },
        )

    def test_case_insensitive_exact_match(self):
        """
        Case-insensitive mode matches regardless of case for exact fields.
        """
        redactor = SensitiveDataRedactor(
            sensitive_fields=["password"], case_insensitive=True
        )

        assert {
            "password": "[REDACTED]",
            "PASSWORD": "[REDACTED]",
            "Password": "[REDACTED]",
            "PaSsWoRd": "[REDACTED]",
            "username": "alice",
        } == redactor(
            None,
            None,
            {
                "password": "a",
                "PASSWORD": "b",
                "Password": "c",
                "PaSsWoRd": "d",
                "username": "alice",
            },
        )

    def test_case_insensitive_pattern(self):
        """
        Case-insensitive mode works with patterns.
        """
        redactor = SensitiveDataRedactor(
            sensitive_fields=["*password*"], case_insensitive=True
        )

        assert {
            "user_password": "[REDACTED]",
            "USER_PASSWORD": "[REDACTED]",
            "UserPassword": "[REDACTED]",
            "username": "alice",
        } == redactor(
            None,
            None,
            {
                "user_password": "a",
                "USER_PASSWORD": "b",
                "UserPassword": "c",
                "username": "alice",
            },
        )

    def test_case_sensitive_by_default(self):
        """
        Case-sensitive matching is the default behavior.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["password"])

        assert {
            "password": "[REDACTED]",
            "PASSWORD": "still_visible",
            "Password": "also_visible",
        } == redactor(
            None,
            None,
            {
                "password": "secret",
                "PASSWORD": "still_visible",
                "Password": "also_visible",
            },
        )

    def test_pattern_in_nested_dict(self):
        """
        Patterns work in nested dictionaries.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["*_key"])

        assert {
            "config": {
                "api_key": "[REDACTED]",
                "secret_key": "[REDACTED]",
                "timeout": 30,
            }
        } == redactor(
            None,
            None,
            {
                "config": {
                    "api_key": "abc",
                    "secret_key": "xyz",
                    "timeout": 30,
                }
            },
        )

    def test_pattern_in_list_of_dicts(self):
        """
        Patterns work in lists of dictionaries.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["*password*"])

        assert {
            "users": [
                {"name": "alice", "user_password": "[REDACTED]"},
                {"name": "bob", "password_hash": "[REDACTED]"},
            ]
        } == redactor(
            None,
            None,
            {
                "users": [
                    {"name": "alice", "user_password": "pass1"},
                    {"name": "bob", "password_hash": "hash2"},
                ]
            },
        )

    def test_pickleable_with_patterns(self):
        """
        An instance with patterns can be pickled and unpickled.
        """
        redactor = SensitiveDataRedactor(
            sensitive_fields=["*password*", "api_*"],
            placeholder="***",
            case_insensitive=True,
        )
        pickled = pickle.dumps(redactor)
        unpickled = pickle.loads(pickled)

        assert {"user_password": "***", "api_key": "***"} == unpickled(
            None, None, {"user_password": "secret", "api_key": "key"}
        )
        # Also verify case insensitive works after unpickling
        assert {"USER_PASSWORD": "***"} == unpickled(
            None, None, {"USER_PASSWORD": "secret"}
        )

    def test_redaction_callback_basic(self):
        """
        A custom redaction callback is used instead of placeholder.
        """

        def custom_redactor(field_name, value, path):
            return f"<redacted:{field_name}>"

        redactor = SensitiveDataRedactor(
            sensitive_fields=["password"],
            redaction_callback=custom_redactor,
        )

        assert {"password": "<redacted:password>"} == redactor(
            None, None, {"password": "secret"}
        )

    def test_redaction_callback_receives_value(self):
        """
        The redaction callback receives the original value.
        """

        def length_redactor(field_name, value, path):
            if isinstance(value, str):
                return f"[{len(value)} chars]"
            return "[REDACTED]"

        redactor = SensitiveDataRedactor(
            sensitive_fields=["password"],
            redaction_callback=length_redactor,
        )

        assert {"password": "[9 chars]"} == redactor(
            None, None, {"password": "secret123"}
        )

    def test_redaction_callback_receives_path(self):
        """
        The redaction callback receives the field path.
        """
        paths_received = []

        def path_collector(field_name, value, path):
            paths_received.append(path)
            return "[REDACTED]"

        redactor = SensitiveDataRedactor(
            sensitive_fields=["password"],
            redaction_callback=path_collector,
        )

        redactor(
            None,
            None,
            {
                "password": "top_level",
                "config": {"password": "nested"},
                "users": [{"password": "in_list"}],
            },
        )

        assert "password" in paths_received
        assert "config.password" in paths_received
        assert "users[0].password" in paths_received

    def test_redaction_callback_with_pattern(self):
        """
        Redaction callback works with pattern matching.
        """

        def custom_redactor(field_name, value, path):
            return f"***{field_name}***"

        redactor = SensitiveDataRedactor(
            sensitive_fields=["*_key"],
            redaction_callback=custom_redactor,
        )

        assert {
            "api_key": "***api_key***",
            "secret_key": "***secret_key***",
        } == redactor(None, None, {"api_key": "abc", "secret_key": "xyz"})

    def test_redaction_callback_overrides_placeholder(self):
        """
        When both callback and placeholder are provided, callback takes precedence.
        """

        def custom_redactor(field_name, value, path):
            return "CUSTOM"

        redactor = SensitiveDataRedactor(
            sensitive_fields=["password"],
            placeholder="PLACEHOLDER",
            redaction_callback=custom_redactor,
        )

        assert {"password": "CUSTOM"} == redactor(
            None, None, {"password": "secret"}
        )

    def test_audit_callback_basic(self):
        """
        Audit callback is called for each redacted field.
        """
        audit_log = []

        def audit(field_name, value, path):
            audit_log.append(
                {"field": field_name, "value": value, "path": path}
            )

        redactor = SensitiveDataRedactor(
            sensitive_fields=["password"],
            audit_callback=audit,
        )

        redactor(None, None, {"user": "alice", "password": "secret"})

        assert len(audit_log) == 1
        assert audit_log[0]["field"] == "password"
        assert audit_log[0]["value"] == "secret"
        assert audit_log[0]["path"] == "password"

    def test_audit_callback_multiple_fields(self):
        """
        Audit callback is called for each redacted field.
        """
        audit_log = []

        def audit(field_name, value, path):
            audit_log.append(path)

        redactor = SensitiveDataRedactor(
            sensitive_fields=["password", "api_key"],
            audit_callback=audit,
        )

        redactor(
            None, None, {"password": "pass", "api_key": "key", "user": "alice"}
        )

        assert len(audit_log) == 2
        assert "password" in audit_log
        assert "api_key" in audit_log

    def test_audit_callback_nested_paths(self):
        """
        Audit callback receives correct paths for nested fields.
        """
        audit_log = []

        def audit(field_name, value, path):
            audit_log.append(path)

        redactor = SensitiveDataRedactor(
            sensitive_fields=["secret"],
            audit_callback=audit,
        )

        redactor(
            None,
            None,
            {
                "secret": "top",
                "config": {"database": {"secret": "nested"}},
                "items": [{"secret": "in_list"}, {"secret": "in_list_2"}],
            },
        )

        assert "secret" in audit_log
        assert "config.database.secret" in audit_log
        assert "items[0].secret" in audit_log
        assert "items[1].secret" in audit_log

    def test_audit_callback_called_before_redaction(self):
        """
        Audit callback receives the original value before redaction.
        """
        original_values = []

        def audit(field_name, value, path):
            original_values.append(value)

        redactor = SensitiveDataRedactor(
            sensitive_fields=["password"],
            audit_callback=audit,
        )

        result = redactor(None, None, {"password": "my_secret_password"})

        assert result["password"] == "[REDACTED]"
        assert original_values == ["my_secret_password"]

    def test_audit_and_redaction_callbacks_together(self):
        """
        Both audit and redaction callbacks can be used together.
        """
        audit_log = []

        def audit(field_name, value, path):
            audit_log.append({"field": field_name, "path": path})

        def custom_redactor(field_name, value, path):
            return f"<{field_name}:hidden>"

        redactor = SensitiveDataRedactor(
            sensitive_fields=["password"],
            redaction_callback=custom_redactor,
            audit_callback=audit,
        )

        result = redactor(None, None, {"password": "secret"})

        assert result == {"password": "<password:hidden>"}
        assert audit_log == [{"field": "password", "path": "password"}]

    def test_audit_callback_with_patterns(self):
        """
        Audit callback works with pattern matching.
        """
        audit_log = []

        def audit(field_name, value, path):
            audit_log.append(field_name)

        redactor = SensitiveDataRedactor(
            sensitive_fields=["*_secret"],
            audit_callback=audit,
        )

        redactor(
            None,
            None,
            {"db_secret": "abc", "api_secret": "xyz", "username": "alice"},
        )

        assert "db_secret" in audit_log
        assert "api_secret" in audit_log
        assert "username" not in audit_log

    def test_field_path_format_deeply_nested(self):
        """
        Field paths are correctly formatted for deeply nested structures.
        """
        paths = []

        def audit(field_name, value, path):
            paths.append(path)

        redactor = SensitiveDataRedactor(
            sensitive_fields=["key"],
            audit_callback=audit,
        )

        redactor(
            None,
            None,
            {
                "a": {
                    "b": {
                        "c": {"key": "value"},
                    },
                },
                "list": [[[{"key": "nested_list"}]]],
            },
        )

        assert "a.b.c.key" in paths
        assert "list[0][0][0].key" in paths

    def test_pickleable_with_callbacks(self):
        """
        An instance with callbacks can be pickled (callbacks are preserved).
        """
        redactor = SensitiveDataRedactor(
            sensitive_fields=["password"],
            redaction_callback=_test_pickle_redactor,
            audit_callback=_test_pickle_audit,
        )

        pickled = pickle.dumps(redactor)
        unpickled = pickle.loads(pickled)

        assert {"password": "***"} == unpickled(
            None, None, {"password": "secret"}
        )

    def test_pickleable_case_insensitive_exact(self):
        """
        An instance with case-insensitive exact matches can be pickled.
        """
        redactor = SensitiveDataRedactor(
            sensitive_fields=["PASSWORD"],
            case_insensitive=True,
        )

        pickled = pickle.dumps(redactor)
        unpickled = pickle.loads(pickled)

        assert {"password": "[REDACTED]"} == unpickled(
            None, None, {"password": "secret"}
        )

    def test_redacts_nested_lists_deeply(self):
        """
        Redacts sensitive fields deeply nested within lists of lists.
        """
        redactor = SensitiveDataRedactor(["password"])
        event = {
            "users": [
                [{"name": "alice", "password": "secret"}],
                {"data": [{"password": "secret"}]}
            ]
        }
        redactor(None, None, event)
        assert event["users"][0][0]["password"] == "[REDACTED]"
        assert event["users"][1]["data"][0]["password"] == "[REDACTED]"

    def test_redacts_mixed_list_types(self):
        """
        Handles lists containing a mix of dicts, lists, and primitives.
        Ensures all branches in _redact_list are covered.
        """
        redactor = SensitiveDataRedactor(["password"])
        event = {
            "data": [
                "string",  # Primitive (elif False -> loop)
                123,       # Primitive (elif False -> loop)
                {"password": "secret"},  # Dict (if True)
                ["nested", {"password": "secret"}],  # List (elif True)
            ]
        }
        redactor(None, None, event)
        assert event["data"][2]["password"] == "[REDACTED]"
        assert event["data"][3][1]["password"] == "[REDACTED]"
        assert event["data"][0] == "string"
        assert event["data"][1] == 123


class TestSensitiveDataRedactorIntegration:
    """Integration tests for SensitiveDataRedactor with full processor chains."""

    def test_with_json_renderer(self):
        """
        SensitiveDataRedactor works correctly with JSONRenderer in a chain.
        """
        redactor = SensitiveDataRedactor(
            sensitive_fields=["password", "api_key", "*_secret"]
        )
        renderer = JSONRenderer()

        # Simulate processor chain
        event_dict = {
            "event": "user_login",
            "user": "alice",
            "password": "s3cr3t",
            "api_key": "abc123",
            "db_secret": "xyz789",
        }

        # Run through redactor first
        redacted = redactor(None, None, event_dict)
        # Then through JSON renderer
        output = renderer(None, None, redacted)

        # Parse the JSON output
        result = json.loads(output)

        assert result["event"] == "user_login"
        assert result["user"] == "alice"
        assert result["password"] == "[REDACTED]"
        assert result["api_key"] == "[REDACTED]"
        assert result["db_secret"] == "[REDACTED]"

    def test_with_json_renderer_nested(self):
        """
        SensitiveDataRedactor handles nested structures with JSONRenderer.
        """
        redactor = SensitiveDataRedactor(
            sensitive_fields=["*password*", "*token*"]
        )
        renderer = JSONRenderer()

        event_dict = {
            "event": "config_loaded",
            "config": {
                "database": {
                    "host": "localhost",
                    "password": "db_pass",
                },
                "auth": {
                    "access_token": "token123",
                    "refresh_token": "refresh456",
                },
            },
        }

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)
        result = json.loads(output)

        assert result["config"]["database"]["host"] == "localhost"
        assert result["config"]["database"]["password"] == "[REDACTED]"
        assert result["config"]["auth"]["access_token"] == "[REDACTED]"
        assert result["config"]["auth"]["refresh_token"] == "[REDACTED]"

    def test_with_json_renderer_list_of_dicts(self):
        """
        SensitiveDataRedactor handles lists of dicts with JSONRenderer.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["password", "ssn"])
        renderer = JSONRenderer()

        event_dict = {
            "event": "batch_process",
            "users": [
                {"name": "alice", "password": "pass1", "ssn": "123-45-6789"},
                {"name": "bob", "password": "pass2", "ssn": "987-65-4321"},
            ],
        }

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)
        result = json.loads(output)

        assert result["users"][0]["name"] == "alice"
        assert result["users"][0]["password"] == "[REDACTED]"
        assert result["users"][0]["ssn"] == "[REDACTED]"
        assert result["users"][1]["name"] == "bob"
        assert result["users"][1]["password"] == "[REDACTED]"
        assert result["users"][1]["ssn"] == "[REDACTED]"

    def test_with_key_value_renderer(self):
        """
        SensitiveDataRedactor works with KeyValueRenderer.
        """
        from structlog.processors import KeyValueRenderer

        redactor = SensitiveDataRedactor(sensitive_fields=["password"])
        renderer = KeyValueRenderer()

        event_dict = {
            "event": "login",
            "user": "alice",
            "password": "secret",
        }

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)

        assert "password='[REDACTED]'" in output
        assert "user='alice'" in output
        assert "secret" not in output

    def test_with_custom_callback_and_json_renderer(self):
        """
        Custom redaction callback works with JSONRenderer.
        """

        def mask_partial(field_name, value, path):
            if isinstance(value, str) and len(value) > 4:
                return f"{value[:2]}***{value[-2:]}"
            return "[REDACTED]"

        redactor = SensitiveDataRedactor(
            sensitive_fields=["password", "api_key"],
            redaction_callback=mask_partial,
        )
        renderer = JSONRenderer()

        event_dict = {
            "event": "auth",
            "password": "mysecretpassword",
            "api_key": "sk_live_abc123xyz",
        }

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)
        result = json.loads(output)

        assert result["password"] == "my***rd"
        assert result["api_key"] == "sk***yz"

    def test_with_audit_callback_and_json_renderer(self):
        """
        Audit callback is invoked when used with JSONRenderer.
        """
        audit_log = []

        def audit(field_name, value, path):
            audit_log.append({"field": field_name, "path": path})

        redactor = SensitiveDataRedactor(
            sensitive_fields=["*password*"],
            audit_callback=audit,
        )
        renderer = JSONRenderer()

        event_dict = {
            "event": "update",
            "old_password": "old123",
            "new_password": "new456",
            "user": "alice",
        }

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)
        result = json.loads(output)

        assert result["old_password"] == "[REDACTED]"
        assert result["new_password"] == "[REDACTED]"
        assert result["user"] == "alice"
        assert len(audit_log) == 2
        assert {"field": "old_password", "path": "old_password"} in audit_log
        assert {"field": "new_password", "path": "new_password"} in audit_log

    def test_multiple_redactors_in_chain(self):
        """
        Multiple SensitiveDataRedactors can be chained together.
        """
        # First redactor for auth fields
        auth_redactor = SensitiveDataRedactor(
            sensitive_fields=["*password*", "*token*"],
            placeholder="[AUTH_REDACTED]",
        )
        # Second redactor for PII
        pii_redactor = SensitiveDataRedactor(
            sensitive_fields=["*email*", "*ssn*"],
            placeholder="[PII_REDACTED]",
        )
        renderer = JSONRenderer()

        event_dict = {
            "event": "user_create",
            "password": "secret",
            "email": "user@example.com",
            "ssn": "123-45-6789",
            "name": "John",
        }

        # Chain: auth_redactor -> pii_redactor -> renderer
        step1 = auth_redactor(None, None, event_dict)
        step2 = pii_redactor(None, None, step1)
        output = renderer(None, None, step2)
        result = json.loads(output)

        assert result["password"] == "[AUTH_REDACTED]"
        assert result["email"] == "[PII_REDACTED]"
        assert result["ssn"] == "[PII_REDACTED]"
        assert result["name"] == "John"

    def test_with_add_log_level(self):
        """
        SensitiveDataRedactor works with add_log_level processor.
        """
        from structlog.processors import add_log_level

        redactor = SensitiveDataRedactor(sensitive_fields=["password"])
        renderer = JSONRenderer()

        event_dict = {"event": "login", "password": "secret"}

        # Simulate: add_log_level -> redactor -> renderer
        step1 = add_log_level(None, "info", event_dict)
        step2 = redactor(None, "info", step1)
        output = renderer(None, "info", step2)
        result = json.loads(output)

        assert result["level"] == "info"
        assert result["password"] == "[REDACTED]"

    def test_case_insensitive_with_json_renderer(self):
        """
        Case-insensitive matching works with JSONRenderer.
        """
        redactor = SensitiveDataRedactor(
            sensitive_fields=["password", "apikey"],
            case_insensitive=True,
        )
        renderer = JSONRenderer()

        event_dict = {
            "event": "config",
            "PASSWORD": "pass1",
            "Password": "pass2",
            "ApiKey": "key1",
            "APIKEY": "key2",
        }

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)
        result = json.loads(output)

        assert result["PASSWORD"] == "[REDACTED]"
        assert result["Password"] == "[REDACTED]"
        assert result["ApiKey"] == "[REDACTED]"
        assert result["APIKEY"] == "[REDACTED]"

    def test_preserves_event_key(self):
        """
        The 'event' key is preserved and not accidentally redacted.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["password"])
        renderer = JSONRenderer()

        event_dict = {
            "event": "user_authenticated",
            "password": "secret",
        }

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)
        result = json.loads(output)

        assert result["event"] == "user_authenticated"
        assert result["password"] == "[REDACTED]"

    def test_with_timestamper(self):
        """
        SensitiveDataRedactor works with TimeStamper processor.
        """
        from structlog.processors import TimeStamper

        timestamper = TimeStamper(fmt="iso")
        redactor = SensitiveDataRedactor(sensitive_fields=["password"])
        renderer = JSONRenderer()

        event_dict = {"event": "login", "password": "secret"}

        # Chain: timestamper -> redactor -> renderer
        step1 = timestamper(None, None, event_dict)
        step2 = redactor(None, None, step1)
        output = renderer(None, None, step2)
        result = json.loads(output)

        assert "timestamp" in result
        assert result["password"] == "[REDACTED]"

    def test_deeply_nested_with_json_renderer(self):
        """
        Deeply nested structures are properly redacted and rendered.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["secret"])
        renderer = JSONRenderer()

        event_dict = {
            "event": "deep_config",
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "secret": "deep_secret",
                            "public": "visible",
                        }
                    }
                }
            },
        }

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)
        result = json.loads(output)

        assert (
            result["level1"]["level2"]["level3"]["level4"]["secret"]
            == "[REDACTED]"
        )
        assert (
            result["level1"]["level2"]["level3"]["level4"]["public"]
            == "visible"
        )

    def test_empty_event_dict_with_renderer(self):
        """
        Empty event dict is handled correctly with renderer.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["password"])
        renderer = JSONRenderer()

        event_dict = {}

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)
        result = json.loads(output)

        assert result == {}

    def test_special_characters_in_values(self):
        """
        Values with special characters are handled correctly.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["password"])
        renderer = JSONRenderer()

        event_dict = {
            "event": "test",
            "password": 'secret with "quotes" and \\backslash',
            "data": "normal",
        }

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)
        result = json.loads(output)

        assert result["password"] == "[REDACTED]"
        assert result["data"] == "normal"

    def test_unicode_field_names_and_values(self):
        """
        Unicode field names and values are handled correctly.
        """
        redactor = SensitiveDataRedactor(sensitive_fields=["密码", "password"])
        renderer = JSONRenderer()

        event_dict = {
            "event": "测试",
            "密码": "秘密",
            "password": "secret",
            "user": "用户",
        }

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)
        result = json.loads(output)

        assert result["密码"] == "[REDACTED]"
        assert result["password"] == "[REDACTED]"
        assert result["user"] == "用户"
        assert result["event"] == "测试"

    def test_with_console_renderer(self):
        """
        SensitiveDataRedactor works with ConsoleRenderer.
        """
        from structlog.dev import ConsoleRenderer

        redactor = SensitiveDataRedactor(
            sensitive_fields=["password", "api_key"]
        )
        renderer = ConsoleRenderer(colors=False)

        event_dict = {
            "event": "user_login",
            "user": "alice",
            "password": "secret123",
            "api_key": "sk_live_xxx",
        }

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)

        # ConsoleRenderer returns a string
        assert "[REDACTED]" in output
        assert "secret123" not in output
        assert "sk_live_xxx" not in output
        assert "alice" in output

    def test_with_console_renderer_nested(self):
        """
        Nested structures work with ConsoleRenderer.
        """
        from structlog.dev import ConsoleRenderer

        redactor = SensitiveDataRedactor(sensitive_fields=["*password*"])
        renderer = ConsoleRenderer(colors=False)

        event_dict = {
            "event": "config",
            "db": {"password": "db_secret"},
        }

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)

        assert "[REDACTED]" in output
        assert "db_secret" not in output

    def test_with_logfmt_renderer(self):
        """
        SensitiveDataRedactor works with LogfmtRenderer.
        """
        from structlog.processors import LogfmtRenderer

        redactor = SensitiveDataRedactor(sensitive_fields=["password"])
        renderer = LogfmtRenderer()

        event_dict = {
            "event": "login",
            "user": "alice",
            "password": "secret",
        }

        redacted = redactor(None, None, event_dict)
        output = renderer(None, None, redacted)

        # LogfmtRenderer produces key=value pairs
        assert "password=[REDACTED]" in output
        assert "user=alice" in output
        assert "secret" not in output

    def test_full_structlog_configuration(self):
        """
        SensitiveDataRedactor works in a full structlog configuration.
        """
        from io import StringIO

        import structlog

        output = StringIO()

        redactor = SensitiveDataRedactor(
            sensitive_fields=["*password*", "*secret*", "*token*", "*key*"],
            case_insensitive=True,
        )

        # Configure structlog with our redactor
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                redactor,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(file=output),
            cache_logger_on_first_use=False,
        )

        log = structlog.get_logger()
        log.info(
            "user_authenticated",
            user="alice",
            password="s3cr3t",
            api_key="abc123",
            session_token="xyz789",
        )

        logged = output.getvalue()
        result = json.loads(logged)

        assert result["user"] == "alice"
        assert result["password"] == "[REDACTED]"
        assert result["api_key"] == "[REDACTED]"
        assert result["session_token"] == "[REDACTED]"
        assert "s3cr3t" not in logged
        assert "abc123" not in logged
        assert "xyz789" not in logged

    def test_with_stdlib_logging_integration(self):
        """
        SensitiveDataRedactor works with stdlib logging integration.
        """
        import logging

        from io import StringIO

        import structlog

        from structlog.stdlib import ProcessorFormatter

        # Create a string stream to capture output
        stream = StringIO()

        # Set up stdlib logging
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)

        redactor = SensitiveDataRedactor(
            sensitive_fields=["password", "api_key"]
        )

        handler.setFormatter(
            ProcessorFormatter(
                # Use foreign_pre_chain for basic setup
                foreign_pre_chain=[
                    structlog.stdlib.add_log_level,
                ],
                # Use main processors list for redaction to ensure it runs
                # after extra attributes are merged (which happens in ProcessorFormatter)
                processors=[
                    _extract_extra,
                    redactor,
                    structlog.processors.JSONRenderer(),
                ],
            )
        )

        logger = logging.getLogger("test_redactor")
        logger.handlers = [handler]
        logger.setLevel(logging.DEBUG)

        # Log with sensitive data
        logger.info(
            "login attempt",
            extra={"password": "secret", "api_key": "key123", "user": "bob"},
        )

        logged = stream.getvalue()

        # The sensitive data should be redacted
        assert "[REDACTED]" in logged
        assert "secret" not in logged
        assert "key123" not in logged

    def test_gdpr_compliance_scenario(self):
        """
        GDPR compliance scenario with PII redaction and audit trail.
        """
        audit_events = []

        def gdpr_audit(field_name, value, path):
            audit_events.append(
                {
                    "field": field_name,
                    "path": path,
                    "value_type": type(value).__name__,
                }
            )

        gdpr_redactor = SensitiveDataRedactor(
            sensitive_fields=[
                "*email*",
                "*phone*",
                "*address*",
                "*name*",
                "*ssn*",
                "*birth*",
            ],
            case_insensitive=True,
            audit_callback=gdpr_audit,
        )
        renderer = JSONRenderer()

        event_dict = {
            "event": "user_registration",
            "user_id": "12345",
            "email_address": "user@example.com",
            "phone_number": "+1-555-123-4567",
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "ssn": "123-45-6789",
            "preferences": {"newsletter": True},
        }

        redacted = gdpr_redactor(None, None, event_dict)
        output = renderer(None, None, redacted)
        result = json.loads(output)

        # All PII should be redacted
        assert result["email_address"] == "[REDACTED]"
        assert result["phone_number"] == "[REDACTED]"
        assert result["full_name"] == "[REDACTED]"
        assert result["date_of_birth"] == "[REDACTED]"
        assert result["ssn"] == "[REDACTED]"
        # Non-PII should be preserved
        assert result["user_id"] == "12345"
        assert result["preferences"]["newsletter"] is True

        # Audit trail should have all redacted fields
        assert len(audit_events) == 5
        audit_fields = {e["field"] for e in audit_events}
        assert "email_address" in audit_fields
        assert "phone_number" in audit_fields
        assert "full_name" in audit_fields
        assert "date_of_birth" in audit_fields
        assert "ssn" in audit_fields

    def test_pci_dss_card_masking_scenario(self):
        """
        PCI-DSS compliance scenario with card number masking.
        """

        def mask_card(field_name, value, path):
            if "card" in field_name.lower() and isinstance(value, str):
                # Show only last 4 digits
                digits = "".join(c for c in value if c.isdigit())
                if len(digits) >= 4:
                    return f"****-****-****-{digits[-4:]}"
            return "[REDACTED]"

        pci_redactor = SensitiveDataRedactor(
            sensitive_fields=["*card*", "*cvv*", "*cvc*"],
            case_insensitive=True,
            redaction_callback=mask_card,
        )
        renderer = JSONRenderer()

        event_dict = {
            "event": "payment_processed",
            "transaction_id": "txn_123",
            "card_number": "4111-1111-1111-1234",
            "card_cvv": "123",
            "amount": 99.99,
        }

        redacted = pci_redactor(None, None, event_dict)
        output = renderer(None, None, redacted)
        result = json.loads(output)

        assert result["card_number"] == "****-****-****-1234"
        assert result["card_cvv"] == "[REDACTED]"
        assert result["transaction_id"] == "txn_123"
        assert result["amount"] == 99.99
        # Original card number should not appear
        assert "4111" not in output
