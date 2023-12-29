# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

from __future__ import annotations

import inspect
import sys

from pathlib import Path
from typing import Any

import pytest

from structlog import tracebacks


def get_next_lineno() -> int:
    return inspect.currentframe().f_back.f_lineno + 1


@pytest.mark.parametrize(("data", "expected"), [(3, "3"), ("spam", "spam")])
def test_save_str(data: Any, expected: str):
    """
    "safe_str()" returns the str repr of an object.
    """
    assert expected == tracebacks.safe_str(data)


def test_safe_str_error():
    """
    "safe_str()" does not fail if __str__() raises an exception.
    """

    class Baam:
        def __str__(self) -> str:
            raise ValueError("BAAM!")

    with pytest.raises(ValueError, match="BAAM!"):
        str(Baam())

    assert "<str-error 'BAAM!'>" == tracebacks.safe_str(Baam())


@pytest.mark.parametrize(
    ("data", "max_len", "expected"),
    [
        (3, None, "3"),
        ("spam", None, "spam"),
        (b"spam", None, "b'spam'"),
        ("bacon", 3, "'bac'+2"),
        ("bacon", 4, "'baco'+1"),
        ("bacon", 5, "bacon"),
    ],
)
def test_to_repr(data: Any, max_len: int | None, expected: str):
    """
    "to_repr()" returns the repr of an object, trimmed to max_len.
    """
    assert expected == tracebacks.to_repr(data, max_string=max_len)


def test_to_repr_error():
    """
    "to_repr()" does not fail if __repr__() raises an exception.
    """

    class Baam:
        def __repr__(self) -> str:
            raise ValueError("BAAM!")

    with pytest.raises(ValueError, match="BAAM!"):
        repr(Baam())

    assert "<repr-error 'BAAM!'>" == tracebacks.to_repr(Baam())


def test_simple_exception():
    """
    Tracebacks are parsed for simple, single exceptions.
    """
    try:
        lineno = get_next_lineno()
        1 / 0
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert [
        tracebacks.Stack(
            exc_type="ZeroDivisionError",
            exc_value="division by zero",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=lineno,
                    name="test_simple_exception",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ] == trace.stacks


def test_raise_hide_cause():
    """
    If "raise ... from None" is used, the trace looks like from a simple
    exception.
    """
    try:
        try:
            1 / 0
        except ArithmeticError:
            lineno = get_next_lineno()
            raise ValueError("onoes") from None
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert [
        tracebacks.Stack(
            exc_type="ValueError",
            exc_value="onoes",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=lineno,
                    name="test_raise_hide_cause",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ] == trace.stacks


def test_raise_with_cause():
    """
    If "raise ... from orig" is used, the orig trace is included and marked as
    cause.
    """
    try:
        try:
            lineno_1 = get_next_lineno()
            1 / 0
        except ArithmeticError as orig_exc:
            lineno_2 = get_next_lineno()
            raise ValueError("onoes") from orig_exc
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert [
        tracebacks.Stack(
            exc_type="ValueError",
            exc_value="onoes",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=lineno_2,
                    name="test_raise_with_cause",
                    line="",
                    locals=None,
                ),
            ],
        ),
        tracebacks.Stack(
            exc_type="ZeroDivisionError",
            exc_value="division by zero",
            syntax_error=None,
            is_cause=True,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=lineno_1,
                    name="test_raise_with_cause",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ] == trace.stacks


def test_raise_with_cause_no_tb():
    """
    If an exception's cause has no traceback, that cause is ignored.
    """
    try:
        lineno = get_next_lineno()
        raise ValueError("onoes") from RuntimeError("I am fake")
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert [
        tracebacks.Stack(
            exc_type="ValueError",
            exc_value="onoes",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=lineno,
                    name="test_raise_with_cause_no_tb",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ] == trace.stacks


def test_raise_nested():
    """
    If an exc is raised during handling another one, the orig trace is
    included.
    """
    try:
        try:
            lineno_1 = get_next_lineno()
            1 / 0
        except ArithmeticError:
            lineno_2 = get_next_lineno()
            raise ValueError("onoes")  # noqa: B904
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert [
        tracebacks.Stack(
            exc_type="ValueError",
            exc_value="onoes",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=lineno_2,
                    name="test_raise_nested",
                    line="",
                    locals=None,
                ),
            ],
        ),
        tracebacks.Stack(
            exc_type="ZeroDivisionError",
            exc_value="division by zero",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=lineno_1,
                    name="test_raise_nested",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ] == trace.stacks


def test_raise_no_msg():
    """
    If exception classes (not instances) are raised, "exc_value" is an empty
    string.
    """
    try:
        lineno = get_next_lineno()
        raise RuntimeError
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert [
        tracebacks.Stack(
            exc_type="RuntimeError",
            exc_value="",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=lineno,
                    name="test_raise_no_msg",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ] == trace.stacks


def test_syntax_error():
    """
    For SyntaxError, extra info about that error is added to the trace.
    """
    try:
        # raises SyntaxError: invalid syntax
        lineno = get_next_lineno()
        eval("2 +* 2")  # noqa: PGH001
    except SyntaxError as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert [
        tracebacks.Stack(
            exc_type="SyntaxError",
            exc_value="invalid syntax (<string>, line 1)",
            syntax_error=tracebacks.SyntaxError_(
                offset=4,
                filename="<string>",
                line="2 +* 2",
                lineno=1,
                msg="invalid syntax",
            ),
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=lineno,
                    name="test_syntax_error",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ] == trace.stacks


def test_filename_with_bracket():
    """
    Filenames with brackets (e.g., "<string>") are handled properly.
    """
    try:
        lineno = get_next_lineno()
        exec(compile("1/0", filename="<string>", mode="exec"))
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert [
        tracebacks.Stack(
            exc_type="ZeroDivisionError",
            exc_value="division by zero",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=lineno,
                    name="test_filename_with_bracket",
                    line="",
                    locals=None,
                ),
                tracebacks.Frame(
                    filename="<string>",
                    lineno=1,
                    name="<module>",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ] == trace.stacks


def test_filename_not_a_file():
    """
    "Invalid" filenames are appended to CWD as if they were actual files.
    """
    try:
        lineno = get_next_lineno()
        exec(compile("1/0", filename="string", mode="exec"))
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert [
        tracebacks.Stack(
            exc_type="ZeroDivisionError",
            exc_value="division by zero",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=lineno,
                    name="test_filename_not_a_file",
                    line="",
                    locals=None,
                ),
                tracebacks.Frame(
                    filename=str(Path.cwd().joinpath("string")),
                    lineno=1,
                    name="<module>",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ] == trace.stacks


def test_show_locals():
    """
    Local variables in each frame can optionally be captured.
    """

    def bar(a):
        print(1 / a)

    def foo(a):
        bar(a)

    try:
        foo(0)
    except Exception as e:
        trace = tracebacks.extract(
            type(e), e, e.__traceback__, show_locals=True
        )

    stack_locals = [f.locals for f in trace.stacks[0].frames]
    # The first frames contain functions with "random" memory addresses,
    # so we only check the variable names:
    assert stack_locals[0].keys() == {"foo", "e", "bar"}
    assert stack_locals[1].keys() == {"a", "bar"}
    assert stack_locals[2] == {"a": "0"}


def test_recursive():
    """
    Recursion errors give a lot of frames but don't break stuff.
    """

    def foo(n):
        return bar(n)

    def bar(n):
        return foo(n)

    try:
        lineno = get_next_lineno()
        foo(1)
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    frames = trace.stacks[0].frames
    trace.stacks[0].frames = []

    assert [
        tracebacks.Stack(
            exc_type="RecursionError",
            exc_value="maximum recursion depth exceeded",
            syntax_error=None,
            is_cause=False,
            frames=[],
        ),
    ] == trace.stacks
    assert (
        len(frames) > sys.getrecursionlimit() - 50
    )  # Buffer for frames from pytest
    assert (
        tracebacks.Frame(
            filename=__file__,
            lineno=lineno,
            name="test_recursive",
        )
        == frames[0]
    )

    # If we run the tests under Python 3.12 with sysmon enabled, it inserts
    # frames at the end.
    if sys.version_info >= (3, 12):
        frames = [f for f in frames if "coverage" not in f.filename]

    # Depending on whether we invoke pytest directly or run tox, either "foo()"
    # or "bar()" is at the end of the stack.
    assert frames[-1] in [
        tracebacks.Frame(
            filename=__file__,
            lineno=lineno - 7,
            name="foo",
        ),
        tracebacks.Frame(
            filename=__file__,
            lineno=lineno - 4,
            name="bar",
        ),
    ]


def test_json_traceback():
    """
    Tracebacks are formatted to JSON with all information.
    """
    try:
        lineno = get_next_lineno()
        1 / 0
    except Exception as e:
        format_json = tracebacks.ExceptionDictTransformer(show_locals=False)
        result = format_json((type(e), e, e.__traceback__))

    assert [
        {
            "exc_type": "ZeroDivisionError",
            "exc_value": "division by zero",
            "frames": [
                {
                    "filename": __file__,
                    "line": "",
                    "lineno": lineno,
                    "locals": None,
                    "name": "test_json_traceback",
                }
            ],
            "is_cause": False,
            "syntax_error": None,
        },
    ] == result


def test_json_traceback_locals_max_string():
    """
    Local variables in each frame are trimmed to locals_max_string.
    """
    try:
        _var = "spamspamspam"
        lineno = get_next_lineno()
        1 / 0
    except Exception as e:
        result = tracebacks.ExceptionDictTransformer(locals_max_string=4)(
            (type(e), e, e.__traceback__)
        )
    assert [
        {
            "exc_type": "ZeroDivisionError",
            "exc_value": "division by zero",
            "frames": [
                {
                    "filename": __file__,
                    "line": "",
                    "lineno": lineno,
                    "locals": {
                        "_var": "'spam'+8",
                        "e": "'Zero'+33",
                        "lineno": str(lineno),
                    },
                    "name": "test_json_traceback_locals_max_string",
                }
            ],
            "is_cause": False,
            "syntax_error": None,
        },
    ] == result


@pytest.mark.parametrize(
    ("max_frames", "expected_frames", "skipped_idx", "skipped_count"),
    [
        (2, 3, 1, 2),
        (3, 3, 1, 2),
        (4, 4, -1, 0),
        (5, 4, -1, 0),
    ],
)
def test_json_traceback_max_frames(
    max_frames: int, expected_frames: int, skipped_idx: int, skipped_count: int
):
    """
    Only max_frames frames are included in the traceback and the skipped frames
    are reported.
    """

    def spam():
        return 1 / 0

    def eggs():
        spam()

    def bacon():
        eggs()

    try:
        bacon()
    except Exception as e:
        format_json = tracebacks.ExceptionDictTransformer(
            show_locals=False, max_frames=max_frames
        )
        result = format_json((type(e), e, e.__traceback__))
        trace = result[0]
        assert len(trace["frames"]) == expected_frames, trace["frames"]
        if skipped_count:
            assert trace["frames"][skipped_idx] == {
                "filename": "",
                "line": "",
                "lineno": -1,
                "locals": None,
                "name": f"Skipped frames: {skipped_count}",
            }
        else:
            assert not any(f["lineno"] == -1 for f in trace["frames"])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"locals_max_string": -1},
        {"max_frames": -1},
        {"max_frames": 0},
        {"max_frames": 1},
    ],
)
def test_json_traceback_value_error(kwargs):
    """
    Wrong arguments to ExceptionDictTransformer raise a ValueError that
    contains the name of the argument..
    """
    with pytest.raises(ValueError, match=next(iter(kwargs.keys()))):
        tracebacks.ExceptionDictTransformer(**kwargs)
