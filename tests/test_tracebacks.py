import sys

from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from structlog import tracebacks


@pytest.mark.parametrize("data, expected", [(3, "3"), ("spam", "spam")])
def test_save_str(data: Any, expected: str):
    """
    "safe_str()" returns the str repr of an object.
    """
    assert tracebacks.safe_str(data) == expected


def test_safe_str_error():
    """
    "safe_str()" does not fail if __str__() raises an exception.
    """

    class Baam:
        def __str__(self) -> str:
            raise ValueError("BAAM!")

    pytest.raises(ValueError, str, Baam())
    assert tracebacks.safe_str(Baam()) == "<str-error 'BAAM!'>"


@pytest.mark.parametrize(
    "data, max_len, expected",
    [
        (3, None, "3"),
        ("spam", None, "spam"),
        (b"spam", None, "b'spam'"),
        ("bacon", 3, "'bac'+2"),
        ("bacon", 4, "'baco'+1"),
        ("bacon", 5, "bacon"),
    ],
)
def test_to_repr(data: Any, max_len: Optional[int], expected: str):
    assert tracebacks.to_repr(data, max_string=max_len) == expected


def test_to_repr_error():
    """
    "to_repr()" does not fail if __repr__() raises an exception.
    """

    class Baam:
        def __repr__(self) -> str:
            raise ValueError("BAAM!")

    pytest.raises(ValueError, repr, Baam())
    assert tracebacks.to_repr(Baam()) == "<repr-error 'BAAM!'>"


def test_simple_exception():
    """
    Tracebacks are parsed for simple, single exceptions.
    """
    try:
        1 / 0
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert trace.stacks == [
        tracebacks.Stack(
            exc_type="ZeroDivisionError",
            exc_value="division by zero",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=65,
                    name="test_simple_exception",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ]


def test_raise_hide_cause():
    """
    If "raise ... from None" is used, the trace looks like from a simple
    exception.
    """
    try:
        try:
            1 / 0
        except ArithmeticError:
            raise ValueError("onoes") from None
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert trace.stacks == [
        tracebacks.Stack(
            exc_type="ValueError",
            exc_value="onoes",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=97,
                    name="test_raise_hide_cause",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ]


def test_raise_with_cause():
    """
    If "raise ... from orig" is used, the orig trace is included and marked as
    cause.
    """
    try:
        try:
            1 / 0
        except ArithmeticError as orig_exc:
            raise ValueError("onoes") from orig_exc
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert trace.stacks == [
        tracebacks.Stack(
            exc_type="ValueError",
            exc_value="onoes",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=129,
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
                    lineno=127,
                    name="test_raise_with_cause",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ]


def test_raise_with_cause_no_tb():
    """
    If an exception's cause has no traceback, that cause is ignored.
    """
    try:
        raise ValueError("onoes") from RuntimeError("I am fake")
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert trace.stacks == [
        tracebacks.Stack(
            exc_type="ValueError",
            exc_value="onoes",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=172,
                    name="test_raise_with_cause_no_tb",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ]


def test_raise_nested():
    """
    If an exc is raised during handling another one, the orig trace is
    included.
    """
    try:
        try:
            1 / 0
        except ArithmeticError:
            raise ValueError("onoes")
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert trace.stacks == [
        tracebacks.Stack(
            exc_type="ValueError",
            exc_value="onoes",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=204,
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
                    lineno=202,
                    name="test_raise_nested",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ]


def test_raise_no_msg():
    """
    If exception classes (not instances) are raised, "exc_value" is an empty
    string.
    """
    try:
        raise RuntimeError
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert trace.stacks == [
        tracebacks.Stack(
            exc_type="RuntimeError",
            exc_value="",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=248,
                    name="test_raise_no_msg",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ]


def test_syntax_error():
    """
    For SyntaxError, extra info about that error is added to the trace.
    """
    try:
        # raises SyntaxError: invalid syntax
        eval("2 +* 2")
    except SyntaxError as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert trace.stacks == [
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
                    lineno=277,
                    name="test_syntax_error",
                    line="",
                    locals=None,
                ),
            ],
        ),
    ]


def test_filename_with_bracket():
    """
    Filenames with brackets (e.g., "<string>") are handled properly.
    """
    try:
        exec(compile("1/0", filename="<string>", mode="exec"))
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert trace.stacks == [
        tracebacks.Stack(
            exc_type="ZeroDivisionError",
            exc_value="division by zero",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=311,
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
    ]


def test_filename_not_a_file():
    """
    "Invalid" filenames are appended to CWD as if they were actual files.
    """
    try:
        exec(compile("1/0", filename="string", mode="exec"))
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    assert trace.stacks == [
        tracebacks.Stack(
            exc_type="ZeroDivisionError",
            exc_value="division by zero",
            syntax_error=None,
            is_cause=False,
            frames=[
                tracebacks.Frame(
                    filename=__file__,
                    lineno=346,
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
    ]


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
        foo(1)
    except Exception as e:
        trace = tracebacks.extract(type(e), e, e.__traceback__)

    frames = trace.stacks[0].frames
    trace.stacks[0].frames = []

    assert trace.stacks == [
        tracebacks.Stack(
            exc_type="RecursionError",
            exc_value="maximum recursion depth exceeded",
            syntax_error=None,
            is_cause=False,
            frames=[],
        ),
    ]
    assert (
        len(frames) > sys.getrecursionlimit() - 50
    )  # Buffer for frames from pytest
    assert frames[0] == tracebacks.Frame(
        filename=__file__,
        lineno=414,
        name="test_recursive",
    )
    # Depending on whether we invoke pytest directly or run tox, either "foo()"
    # or "bar()" is at the end of the stack.
    assert frames[-1] in [
        tracebacks.Frame(
            filename=__file__,
            lineno=408,
            name="foo",
        ),
        tracebacks.Frame(
            filename=__file__,
            lineno=411,
            name="bar",
        ),
    ]


def test_json_traceback():
    try:
        1 / 0
    except Exception as e:
        format_json = tracebacks.ExceptionDictTransformer(show_locals=False)
        result = format_json((type(e), e, e.__traceback__))
        assert result == [
            {
                "exc_type": "ZeroDivisionError",
                "exc_value": "division by zero",
                "frames": [
                    {
                        "filename": __file__,
                        "line": "",
                        "lineno": 456,
                        "locals": None,
                        "name": "test_json_traceback",
                    }
                ],
                "is_cause": False,
                "syntax_error": None,
            },
        ]


def test_json_traceback_locals_max_string():
    try:
        _var = "spamspamspam"  # noqa
        1 / 0
    except Exception as e:
        result = tracebacks.ExceptionDictTransformer(locals_max_string=4)(
            (type(e), e, e.__traceback__)
        )
        assert result == [
            {
                "exc_type": "ZeroDivisionError",
                "exc_value": "division by zero",
                "frames": [
                    {
                        "filename": __file__,
                        "line": "",
                        "lineno": 482,
                        "locals": {
                            "_var": "'spam'+8",
                            "e": "'Zero'+33",
                        },
                        "name": "test_json_traceback_locals_max_string",
                    }
                ],
                "is_cause": False,
                "syntax_error": None,
            },
        ]


@pytest.mark.parametrize(
    "max_frames, expected_frames, skipped_idx, skipped_count",
    [
        # (0, 1, 0, 3),
        # (1, 1, 0, 3),
        (2, 3, 1, 2),
        (3, 3, 1, 2),
        (4, 4, -1, 0),
        (5, 4, -1, 0),
    ],
)
def test_json_traceback_max_frames(
    max_frames: int, expected_frames: int, skipped_idx: int, skipped_count: int
):
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
def test_json_traceback_value_error(kwargs: Dict[str, Any]):
    pytest.raises(ValueError, tracebacks.ExceptionDictTransformer, **kwargs)
