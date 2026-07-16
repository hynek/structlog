# SPDX-License-Identifier: MIT OR Apache-2.0
"""Custom filtering of dict traceback locals.

Used from docs/recipes.md via literalinclude.
"""

from structlog.tracebacks import ExceptionDictTransformer


def redact_locals(frame_locals):
    return {
        k: (v if k not in ("token", "password") else "<REDACTED>")
        for k, v in frame_locals.items()
    }


def redact_frames(exc_dict):
    for frame in exc_dict["frames"]:
        if "locals" in frame:
            frame["locals"] = redact_locals(frame["locals"])
    return exc_dict


class RedactingExceptionDictTransformer(ExceptionDictTransformer):
    def __call__(self, exc_info):
        exceptions = super().__call__(exc_info)
        return [redact_frames(exc) for exc in exceptions]
