# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import pytest

from structlog.contextvars import (
    bind_context_local,
    clear_context_local,
    merge_context_local,
    unbind_context_local,
)


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


class TestNewContextvars(object):
    async def test_bind(self, event_loop):
        """
        Binding a variable causes it to be included in the result of
        merge_context_local.
        """

        async def coro():
            bind_context_local(a=1)
            return merge_context_local(None, None, {"b": 2})

        assert {"a": 1, "b": 2} == await event_loop.create_task(coro())

    async def test_multiple_binds(self, event_loop):
        """
        Multiple calls to bind_context_local accumulate values instead of
        replacing them. But they override redefined ones.
        """

        async def coro():
            bind_context_local(a=1, c=3)
            bind_context_local(c=333, d=4)
            return merge_context_local(None, None, {"b": 2})

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
            bind_context_local(a=1)
            await event_loop.create_task(nested_coro())
            return merge_context_local(None, None, {"b": 2})

        async def nested_coro():
            bind_context_local(c=3)

        assert {"a": 1, "b": 2, "c": 3} == await event_loop.create_task(coro())

    async def test_merge_works_without_bind(self, event_loop):
        """
        merge_context_local returns values as normal even when there has
        been no previous calls to bind_context_local.
        """

        async def coro():
            return merge_context_local(None, None, {"b": 2})

        assert {"b": 2} == await event_loop.create_task(coro())

    async def test_merge_overrides_bind(self, event_loop):
        """
        Variables included in merge_context_local override previously bound
        variables.
        """

        async def coro():
            bind_context_local(a=1)
            return merge_context_local(None, None, {"a": 111, "b": 2})

        assert {"a": 111, "b": 2} == await event_loop.create_task(coro())

    async def test_clear(self, event_loop):
        """
        The context-local context can be cleared, causing any previously bound
        variables to not be included in merge_context_local's result.
        """

        async def coro():
            bind_context_local(a=1)
            clear_context_local()
            return merge_context_local(None, None, {"b": 2})

        assert {"b": 2} == await event_loop.create_task(coro())

    async def test_clear_without_bind(self, event_loop):
        """
        The context-local context can be cleared, causing any previously bound
        variables to not be included in merge_context_local's result.
        """

        async def coro():
            clear_context_local()
            return merge_context_local(None, None, {})

        assert {} == await event_loop.create_task(coro())

    async def test_undbind(self, event_loop):
        """
        Unbinding a previously bound variable causes it to be removed from the
        result of merge_context_local.
        """

        async def coro():
            bind_context_local(a=1)
            unbind_context_local("a")
            return merge_context_local(None, None, {"b": 2})

        assert {"b": 2} == await event_loop.create_task(coro())

    async def test_undbind_not_bound(self, event_loop):
        """
        Unbinding a not bound variable causes doesn't raise an exception.
        """

        async def coro():
            unbind_context_local("a")
            return merge_context_local(None, None, {"b": 2})

        assert {"b": 2} == await event_loop.create_task(coro())
