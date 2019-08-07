from typing import Any, Callable, Dict, List, Type, Union

from mypy_extensions import TypedDict

from ._base import BoundLoggerBase
from .dev import _ColorfulStyles, _PlainStyles


EventDict = Dict[str, Any]
ProcessorResult = Union[EventDict, tuple, str]
Processor = Callable[[Any, str, ProcessorResult], ProcessorResult]
LoggingStyles = Union[Type[_ColorfulStyles], Type[_PlainStyles]]

ConfigDict = TypedDict(
    "ConfigDict",
    {
        "processors": List[Processor],
        "context_class": Type,
        "wrapper_class": Type[BoundLoggerBase],
        "logger_factory": Callable[..., Any],
        "cache_logger_on_first_use": bool,
    },
)
