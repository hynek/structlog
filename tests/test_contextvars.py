# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import pytest

from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
    merge_contextvars,
    unbind_contextvars,
)


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


class TestNewContextvars(object):
    async def test_bind(self, event_loop):
        """
        Binding a variable causes it to be included in the result of
        merge_contextvars.
        """

        async def coro():
            bind_contextvars(a=1)
            return merge_contextvars(None, None, {"b": 2})

        assert {"a": 1, "b": 2} == await event_loop.create_task(coro())

    async def test_multiple_binds(self, event_loop):
        """
        Multiple calls to bind_contextvars accumulate values instead of
        replacing them. But they override redefined ones.
        """

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

    async def test_nested_async_bind(self, event_loop):
        """
        Context is passed correctly between "nested" concurrent operations.
        """

        async def coro():
            bind_contextvars(a=1)
            await event_loop.create_task(nested_coro())
            return merge_contextvars(None, None, {"b": 2})

        async def nested_coro():
            bind_contextvars(c=3)

        assert {"a": 1, "b": 2, "c": 3} == await event_loop.create_task(coro())

    async def test_merge_works_without_bind(self, event_loop):
        """
        merge_contextvars returns values as normal even when there has
        been no previous calls to bind_contextvars.
        """

        async def coro():
            return merge_contextvars(None, None, {"b": 2})

        assert {"b": 2} == await event_loop.create_task(coro())

    async def test_merge_overrides_bind(self, event_loop):
        """
        Variables included in merge_contextvars override previously
        bound variables.
        """

        async def coro():
            bind_contextvars(a=1)
            return merge_contextvars(None, None, {"a": 111, "b": 2})

        assert {"a": 111, "b": 2} == await event_loop.create_task(coro())

    async def test_clear(self, event_loop):
        """
        The context-local context can be cleared, causing any previously bound
        variables to not be included in merge_contextvars's result.
        """

        async def coro():
            bind_contextvars(a=1)
            clear_contextvars()
            return merge_contextvars(None, None, {"b": 2})

        assert {"b": 2} == await event_loop.create_task(coro())

    async def test_clear_without_bind(self, event_loop):
        """
        The context-local context can be cleared, causing any previously bound
        variables to not be included in merge_contextvars's result.
        """

        async def coro():
            clear_contextvars()
            return merge_contextvars(None, None, {})

        assert {} == await event_loop.create_task(coro())

    async def test_undbind(self, event_loop):
        """
        Unbinding a previously bound variable causes it to be removed from the
        result of merge_contextvars.
        """

        async def coro():
            bind_contextvars(a=1)
            unbind_contextvars("a")
            return merge_contextvars(None, None, {"b": 2})

        assert {"b": 2} == await event_loop.create_task(coro())

    async def test_undbind_not_bound(self, event_loop):
        """
        Unbinding a not bound variable causes doesn't raise an exception.
        """

        async def coro():
            unbind_contextvars("a")
            return merge_contextvars(None, None, {"b": 2})

        assert {"b": 2} == await event_loop.create_task(coro())
