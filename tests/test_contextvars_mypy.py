from mypy import api

import structlog

from structlog.contextvars import bound_contextvars, merge_contextvars


structlog.configure(processors=[merge_contextvars, structlog.processors.KeyValueRenderer()])

class TestBoundContextHint:

    def context_manager_usage(self):
        with bound_contextvars(a=1):
            ...


    @bound_contextvars(a=2)
    def decorator_usage(self):
        ...

    def test_bound_contextvars(self):
        MYPY_ARGS = [
            "--config-file", "pyproject.toml",
            "tests/test_contextvars_mypy.py",
        ]
        stdout, stderr, exit_status = api.run(MYPY_ARGS)
        assert exit_status == 0, (
            "Mypy stub type error:\n"
            f"{stdout}\n"
            f"{stderr}"
        )

