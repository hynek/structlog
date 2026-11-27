# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import asyncio
import inspect
import secrets

import pytest

import structlog

from structlog.contextvars import (
    _CONTEXT_VARS,
    bind_contextvars,
    bound_contextvars,
    clear_contextvars,
    get_contextvars,
    get_merged_contextvars,
    merge_contextvars,
    reset_contextvars,
    unbind_contextvars,
)


@pytest.fixture(autouse=True)
def _clear_contextvars():
    """
    Make sure all tests start with a clean slate.
    """
    clear_contextvars()


class TestContextvars:
    async def test_bind(self):
        """
        Binding a variable causes it to be included in the result of
        merge_contextvars.
        """
        event_loop = asyncio.get_running_loop()

        async def coro():
            bind_contextvars(a=1)
            return merge_contextvars(None, None, {"b": 2})

        assert {"a": 1, "b": 2} == await event_loop.create_task(coro())

    async def test_multiple_binds(self):
        """
        Multiple calls to bind_contextvars accumulate values instead of
        replacing them. But they override redefined ones.
        """
        event_loop = asyncio.get_running_loop()

        async def coro():
            bind_contextvars(a=1, c=3)
            bind_contextvars(c=333, d=4)
            return merge_contextvars(None, None, {"b": 2})

        assert {
            "a": 1,
            "b": 2,
            "c": 333,
            "d": 4,
        } == await event_loop.create_task(coro())

    async def test_reset(self):
        """
        reset_contextvars allows resetting contexvars to
        previously-set values.
        """
        event_loop = asyncio.get_running_loop()

        async def coro():
            bind_contextvars(a=1)

            assert {"a": 1} == get_contextvars()

            await event_loop.create_task(nested_coro())

        async def nested_coro():
            tokens = bind_contextvars(a=2, b=3)

            assert {"a": 2, "b": 3} == get_contextvars()

            reset_contextvars(**tokens)

            assert {"a": 1} == get_contextvars()

        await event_loop.create_task(coro())

    async def test_nested_async_bind(self):
        """
        Context is passed correctly between "nested" concurrent operations.
        """
        event_loop = asyncio.get_running_loop()

        async def coro():
            bind_contextvars(a=1)
            return await event_loop.create_task(nested_coro())

        async def nested_coro():
            bind_contextvars(c=3)
            return merge_contextvars(None, None, {"b": 2})

        assert {"a": 1, "b": 2, "c": 3} == await event_loop.create_task(coro())

    async def test_merge_works_without_bind(self):
        """
        merge_contextvars returns values as normal even when there has
        been no previous calls to bind_contextvars.
        """
        event_loop = asyncio.get_running_loop()

        async def coro():
            return merge_contextvars(None, None, {"b": 2})

        assert {"b": 2} == await event_loop.create_task(coro())

    async def test_merge_overrides_bind(self):
        """
        Variables included in merge_contextvars override previously
        bound variables.
        """
        event_loop = asyncio.get_running_loop()

        async def coro():
            bind_contextvars(a=1)
            return merge_contextvars(None, None, {"a": 111, "b": 2})

        assert {"a": 111, "b": 2} == await event_loop.create_task(coro())

    async def test_clear(self):
        """
        The context-local context can be cleared, causing any previously bound
        variables to not be included in merge_contextvars's result.
        """
        event_loop = asyncio.get_running_loop()

        async def coro():
            bind_contextvars(a=1)
            clear_contextvars()
            return merge_contextvars(None, None, {"b": 2})

        assert {"b": 2} == await event_loop.create_task(coro())

    async def test_clear_without_bind(self):
        """
        The context-local context can be cleared, causing any previously bound
        variables to not be included in merge_contextvars's result.
        """
        event_loop = asyncio.get_running_loop()

        async def coro():
            clear_contextvars()
            return merge_contextvars(None, None, {})

        assert {} == await event_loop.create_task(coro())

    async def test_unbind(self):
        """
        Unbinding a previously bound variable causes it to be removed from the
        result of merge_contextvars.
        """
        event_loop = asyncio.get_running_loop()

        async def coro():
            bind_contextvars(a=1)
            unbind_contextvars("a")
            return merge_contextvars(None, None, {"b": 2})

        assert {"b": 2} == await event_loop.create_task(coro())

    async def test_unbind_not_bound(self):
        """
        Unbinding a not bound variable causes doesn't raise an exception.
        """
        event_loop = asyncio.get_running_loop()

        async def coro():
            # Since unbinding means "setting to Ellipsis", we have to make
            # some effort to ensure that the ContextVar never existed.
            unbind_contextvars("a" + secrets.token_hex())

            return merge_contextvars(None, None, {"b": 2})

        assert {"b": 2} == await event_loop.create_task(coro())

    async def test_parallel_binds(self):
        """
        Binding a variable causes it to be included in the result of
        merge_contextvars.
        """
        event_loop = asyncio.get_running_loop()
        coro1_bind = asyncio.Event()
        coro2_bind = asyncio.Event()

        bind_contextvars(c=3)

        async def coro1():
            bind_contextvars(a=1)

            coro1_bind.set()
            await coro2_bind.wait()

            return merge_contextvars(None, None, {"b": 2})

        async def coro2():
            bind_contextvars(a=2)

            await coro1_bind.wait()
            coro2_bind.set()

            return merge_contextvars(None, None, {"b": 2})

        coro1_task = event_loop.create_task(coro1())
        coro2_task = event_loop.create_task(coro2())

        assert {"a": 1, "b": 2, "c": 3} == await coro1_task
        assert {"a": 2, "b": 2, "c": 3} == await coro2_task

    def test_get_only_gets_structlog_without_deleted(self):
        """
        get_contextvars returns only the structlog-specific key-values with
        the prefix removed. Deleted keys (= Ellipsis) are ignored.
        """
        bind_contextvars(a=1, b=2)
        unbind_contextvars("b")
        _CONTEXT_VARS["foo"] = "bar"

        assert {"a": 1} == get_contextvars()

    def test_get_merged_merges_context(self):
        """
        get_merged_contextvars merges a bound context into the copy.
        """
        bind_contextvars(x=1)
        log = structlog.get_logger().bind(y=2)

        assert {"x": 1, "y": 2} == get_merged_contextvars(log)

    def test_concurrent_first_bind_creates_single_var(self, monkeypatch):
        """
        Concurrent first binds of the same key create exactly one
        ContextVar.

        Regression test for #851: without the creation lock, every racing
        thread builds its own ContextVar and all but one are orphaned
        (leaked). Worse, threads that bound on an orphaned var then fail in
        reset_contextvars() with ValueError ("Token was created by a
        different ContextVar").

        The patched ContextVar factory parks every racing thread on a
        barrier inside the creation window, so the race is deterministic.
        """
        import contextvars as stdlib_contextvars
        import threading
        import time

        n_threads = 8
        key = f"thread_race_{secrets.token_hex(8)}"
        structlog_key = f"structlog_{key}"
        assert structlog_key not in _CONTEXT_VARS

        creation_barrier = threading.Barrier(n_threads)
        real_contextvar = stdlib_contextvars.ContextVar
        creations = []

        def racy_factory(name, *, default=None):
            if name == structlog_key:
                creations.append(name)
                # Widen the creation window so every racing thread is
                # inside it at once. (A barrier here would deadlock
                # against the fix, which serializes creation.)
                time.sleep(0.2)

            return real_contextvar(name, default=default)

        monkeypatch.setattr(stdlib_contextvars, "ContextVar", racy_factory)

        bound_barrier = threading.Barrier(n_threads)
        reset_barrier = threading.Barrier(n_threads)
        errors = []

        def worker(i):
            try:
                # Line up all threads before the first bind, so they all
                # race the ContextVar creation window together.
                creation_barrier.wait(timeout=30)
                tokens = bind_contextvars(**{key: i})
                # Wait until every bind (and therefore every losing
                # assignment) has happened before resetting, so a raced
                # bind deterministically surfaces as a ValueError.
                bound_barrier.wait(timeout=30)
                reset_barrier.wait(timeout=30)
                reset_contextvars(**tokens)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=worker, args=(i,))
            for i in range(n_threads)
        ]
        try:
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=60)

            assert not any(t.is_alive() for t in threads)
            assert 1 == len(creations)
            assert [] == errors
        finally:
            _CONTEXT_VARS.pop(structlog_key, None)


class TestBoundContextvars:
    def test_cleanup(self):
        """
        Bindings are cleaned up
        """
        with bound_contextvars(x=42, y="foo"):
            assert {"x": 42, "y": "foo"} == get_contextvars()

        assert {} == get_contextvars()

    def test_cleanup_conflict(self):
        """
        Overwritten keys are restored after the clean up
        """
        bind_contextvars(x="original", z="unrelated")
        with bound_contextvars(x=42, y="foo"):
            assert {"x": 42, "y": "foo", "z": "unrelated"} == get_contextvars()

        assert {"x": "original", "z": "unrelated"} == get_contextvars()

    def test_preserve_independent_bind(self):
        """
        New bindings inside bound_contextvars are preserved after the clean up
        """
        with bound_contextvars(x=42):
            bind_contextvars(y="foo")
            assert {"x": 42, "y": "foo"} == get_contextvars()

        assert {"y": "foo"} == get_contextvars()

    def test_nesting_works(self):
        """
        bound_contextvars binds and unbinds even when nested
        """
        with bound_contextvars(l1=1):
            assert {"l1": 1} == get_contextvars()

            with bound_contextvars(l2=2):
                assert {"l1": 1, "l2": 2} == get_contextvars()

            assert {"l1": 1} == get_contextvars()

        assert {} == get_contextvars()

    def test_as_decorator(self):
        """
        bound_contextvars can be used as a decorator and it preserves the
        name, signature and documentation of the wrapped function.
        """

        @bound_contextvars(x=42)
        def wrapped(arg1):
            """Wrapped documentation"""
            bind_contextvars(y=arg1)
            assert {"x": 42, "y": arg1} == get_contextvars()

        wrapped(23)

        assert "wrapped" == wrapped.__name__
        assert "(arg1)" == str(inspect.signature(wrapped))
        assert "Wrapped documentation" == wrapped.__doc__
