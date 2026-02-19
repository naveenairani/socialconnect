"""
Generic async Cursor for pagination across all providers.

Supports dot-path token extraction so it works with any API shape:
  - X API: "meta.next_token"
  - Telegram: "next_cursor"
  - Custom: any dot-separated path into the response dict/model
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any


def _extract_nested(obj: Any, path: str) -> Any:
    """Extract a value from a nested dict/object using a dot-separated path."""
    parts = path.split(".")
    for part in parts:
        if obj is None:
            return None
        obj = obj.get(part) if isinstance(obj, dict) else getattr(obj, part, None)
    return obj


class Cursor:
    """
    Provider-agnostic async cursor for paginated API calls.

    Wraps any async callable that accepts a ``pagination_token`` kwarg
    (or a custom ``token_param``) and returns a page of results.

    Example::

        cursor = Cursor(
            adapter.get_tweets,
            next_token_field="meta.next_token",
            data_field="data",
        )
        async for tweet in cursor.items(limit=200):
            print(tweet)

        async for page in cursor.pages(limit=5):
            print(len(page["data"]))
    """

    def __init__(
        self,
        method: Callable[..., Any],
        *args: Any,
        next_token_field: str = "meta.next_token",
        data_field: str = "data",
        token_param: str = "pagination_token",
        **kwargs: Any,
    ) -> None:
        """
        Args:
            method: Any async callable returning a dict or Pydantic model per page.
            *args: Positional args forwarded to ``method`` on every call.
            next_token_field: Dot-path to the pagination token in the response.
            data_field: Dot-path to the list of items in the response.
            token_param: Kwarg name used to pass the pagination token to ``method``.
            **kwargs: Base kwargs forwarded to ``method`` (token kwarg is added on top).
        """
        self._method = method
        self._args = args
        self._kwargs = kwargs
        self._next_token_field = next_token_field
        self._data_field = data_field
        self._token_param = token_param

    async def pages(self, limit: int | None = None) -> AsyncIterator[Any]:
        """Async-iterate over raw page responses."""
        token: str | None = None
        count = 0
        while True:
            if limit is not None and count >= limit:
                break
            kwargs = dict(self._kwargs)
            if token:
                kwargs[self._token_param] = token
            page = await self._method(*self._args, **kwargs)
            yield page
            count += 1
            token = _extract_nested(page, self._next_token_field)
            if not token:
                break

    async def items(self, limit: int | None = None) -> AsyncIterator[Any]:
        """Async-iterate over individual items across all pages."""
        count = 0
        async for page in self.pages():
            items = _extract_nested(page, self._data_field)
            if not isinstance(items, list):
                items = []
            for item in items:
                if limit is not None and count >= limit:
                    return
                yield item
                count += 1
