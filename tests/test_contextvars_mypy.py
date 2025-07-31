from mypy import api

import structlog

from structlog.contextvars import bound_contextvars, merge_contextvars


structlog.configure(
    processors=[merge_contextvars, structlog.processors.KeyValueRenderer()]
)


class TestBoundContextHint:
    def context_manager_usage(self):
        """Example usage of bound_contextvars as a context manager."""
        with bound_contextvars(a=1):
            ...

    @bound_contextvars(a=2)
    def decorator_usage(self):
        """Example usage of bound_contextvars as a decorator."""
        ...

    def test_bound_contextvars(self):
        """Test that bound_contextvars can be used as a context manager and a decorator."""
        MYPY_ARGS = [
            "--config-file",
            "pyproject.toml",
            "tests/test_contextvars_mypy.py",
        ]
        stdout, stderr, exit_status = api.run(MYPY_ARGS)
        assert exit_status == 0, f"Mypy stub type error:\n{stdout}\n{stderr}"
