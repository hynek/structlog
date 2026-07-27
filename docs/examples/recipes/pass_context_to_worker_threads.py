# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pass contextvars into worker threads.

Used from docs/recipes.md via literalinclude.

Requires the optional *pathos* package for ThreadPool.
"""

from functools import partial

from pathos.threading import ThreadPool

import structlog

from structlog.contextvars import bind_contextvars


logger = structlog.get_logger(__name__)


def do_some_work(ctx, this_worker):
    bind_contextvars(**ctx)
    logger.info("WorkerDidSomeWork", worker=this_worker)


def structlog_with_threadpool(f):
    ctx = structlog.contextvars.get_contextvars()
    func = partial(f, ctx)
    workers = ["1", "2", "3"]

    with ThreadPool() as pool:
        return list(pool.map(func, workers))


def manager(request_id: str):
    bind_contextvars(request_id=request_id)
    logger.info("StartingWorkers")
    structlog_with_threadpool(do_some_work)
