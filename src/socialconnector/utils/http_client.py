from typing import Any

import httpx


class HTTPClient:
    """Shared HTTP client wrapper for centered resource management."""

    def __init__(self, timeout: float = 30.0, **kwargs: Any) -> None:
        self.client = httpx.AsyncClient(timeout=timeout, **kwargs)

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self.client.aclose()

    async def request(
        self, method: str, url: str, *, headers: dict[str, str] | None = None, json: Any = None, **kwargs: Any
    ) -> httpx.Response:
        """Make an async HTTP request."""
        # Ensure Content-Type is set for JSON
        if json is not None:
            headers = headers or {}
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"

        return await self.client.request(method, url, headers=headers, json=json, **kwargs)
