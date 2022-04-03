"""
Extract a structured traceback from an exception.

Copied and adapted from Rich:
https://github.com/Textualize/rich/blob/972dedff/rich/traceback.py
"""
import os
import sys
from dataclasses import asdict, dataclass, field
from traceback import walk_tb
from types import TracebackType
from typing import Any, Optional, Type, Union


SHOW_LOCALS = True
LOCALS_MAX_STRING = 80
MAX_FRAMES = 50

ExcInfo = tuple[Type[BaseException], BaseException, Optional[TracebackType]]
OptExcInfo = Union[ExcInfo, tuple[None, None, None]]


@dataclass
class Frame:
    filename: str
    lineno: int
    name: str
    line: str = ""
    locals: Optional[dict[str, str]] = None


@dataclass
class SyntaxError_:  # pylint: disable=invalid-name
    offset: int
    filename: str
    line: str
    lineno: int
    msg: str


@dataclass
class Stack:
    exc_type: str
    exc_value: str
    syntax_error: Optional[SyntaxError_] = None
    is_cause: bool = False
    frames: list[Frame] = field(default_factory=list)


@dataclass
class Trace:
    stacks: list[Stack]


def safe_str(_object: Any) -> str:
    """Don't allow exceptions from __str__ to propegate."""
    try:
        return str(_object)
    except Exception as error:
        return f"<str-error {str(error)!r}>"


def to_repr(obj: Any, max_string: Optional[int] = None) -> str:
    """Get repr string for an object, but catch errors."""
    if isinstance(obj, str):
        obj_repr = obj
    else:
        try:
            obj_repr = repr(obj)
        except Exception as error:
            obj_repr = f"<repr-error {str(error)!r}>"

    if max_string is not None and len(obj_repr) > max_string:
        truncated = len(obj_repr) - max_string
        obj_repr = f"{obj_repr[:max_string]!r}+{truncated}"

    return obj_repr


def extract(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    traceback: Optional[TracebackType],
    *,
    show_locals: bool = False,
    locals_max_string: int = LOCALS_MAX_STRING,
) -> Trace:
    """
    Extract traceback information.

    Args:
        exc_type: Exception type.
        exc_value: Exception value.
        traceback: Python Traceback object.
        show_locals: Enable display of local variables. Defaults to False.
        locals_max_string: Maximum length of string before truncating, or ``None`` to
            disable.
        max_frames: Maximum number of frames in each stack

    Returns:
        Trace: A Trace instance which you can use to construct a :cls:`Traceback`.
    """

    stacks: list[Stack] = []
    is_cause = False

    while True:
        stack = Stack(
            exc_type=safe_str(exc_type.__name__),
            exc_value=safe_str(exc_value),
            is_cause=is_cause,
        )

        if isinstance(exc_value, SyntaxError):
            stack.syntax_error = SyntaxError_(
                offset=exc_value.offset or 0,
                filename=exc_value.filename or "?",
                lineno=exc_value.lineno or 0,
                line=exc_value.text or "",
                msg=exc_value.msg,
            )

        stacks.append(stack)
        append = stack.frames.append  # pylint: disable=no-member

        for frame_summary, line_no in walk_tb(traceback):
            filename = frame_summary.f_code.co_filename
            if filename and not filename.startswith("<"):
                filename = os.path.abspath(filename)
            frame = Frame(
                filename=filename or "?",
                lineno=line_no,
                name=frame_summary.f_code.co_name,
                locals={
                    key: to_repr(value, max_string=locals_max_string)
                    for key, value in frame_summary.f_locals.items()
                }
                if show_locals
                else None,
            )
            append(frame)

        cause = getattr(exc_value, "__cause__", None)
        if cause and cause.__traceback__:
            exc_type = cause.__class__
            exc_value = cause
            traceback = cause.__traceback__
            is_cause = True
            continue

        cause = exc_value.__context__
        if (
            cause
            and cause.__traceback__
            and not getattr(exc_value, "__suppress_context__", False)
        ):
            exc_type = cause.__class__
            exc_value = cause
            traceback = cause.__traceback__
            is_cause = False
            continue

        # No cover, code is reached but coverage doesn't recognize it.
        break  # pragma: no cover

    trace = Trace(stacks=stacks)
    return trace


def get_exc_info(v: Any) -> OptExcInfo:
    """
    Return an exception info tuple for the input value.

    Args:
        v: Usually an :exc:`BaseException` instance or an exception tuple
            ``(exc_cls, exc_val, traceback)``.  If it is someting ``True``-ish, use
            :func:`sys.exc_info()` to get the exception info.

    Return:
        An exception info tuple or ``(None, None, None)`` if there was no exception.
    """
    if isinstance(v, BaseException):
        return (type(v), v, v.__traceback__)

    if isinstance(v, tuple):
        return v  # type: ignore

    if v:
        return sys.exc_info()

    return (None, None, None)


def get_traceback_dicts(
    exception: Any,
    show_locals: bool = True,
    locals_max_string: int = LOCALS_MAX_STRING,
    max_frames: int = MAX_FRAMES,
) -> list[dict[str, Any]]:
    """
    Return a list of exception stack dictionaries for *exception*.

    These dictionaries are based on :cls:`Stack` instances generated by
    :func:`extract()` and can be dumped to JSON.
    """
    if locals_max_string < 0:
        raise ValueError(f'"locals_max_string" must be >= 0: {locals_max_string}')
    if max_frames < 2:
        raise ValueError(f'"max_frames" must be >= 2: {max_frames}')

    exc_info = get_exc_info(exception)
    if exc_info == (None, None, None):
        return []

    trace = extract(
        *exc_info, show_locals=show_locals, locals_max_string=locals_max_string
    )

    for stack in trace.stacks:
        if len(stack.frames) <= max_frames:
            continue

        half = max_frames // 2  # Force int division to handle odd numbers correctly
        fake_frame = Frame(
            filename="",
            lineno=-1,
            name=f"Skipped frames: {len(stack.frames) - (2 * half)}",
        )
        stack.frames[:] = [*stack.frames[:half], fake_frame, *stack.frames[-half:]]

    stack_dicts = [asdict(stack) for stack in trace.stacks]
    return stack_dicts
