"""
X HTTP Mixin for unified request handling and pagination.
"""

from typing import Any

from socialconnector.core.exceptions import RateLimitError
from socialconnector.core.models import PaginatedResult


class XHttpMixin:
    """Mixin providing unified request and pagination logic for X API."""

    BASE_URL = "https://api.x.com/2"

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        files: dict[str, Any] | None = None,
        auth_type: str | None = None,  # "oauth1" or "oauth2"
    ) -> Any:
        """Unified request handler with auth dispatch and rate-limit handling."""
        # Build URL
        url = path if path.startswith("http") else f"{self.BASE_URL.strip()}/{path.lstrip('/')}"

        # Determine strategy: passed auth_type or default self.auth_strategy
        current_strategy = auth_type or self.auth_strategy

        if current_strategy == "oauth1":
            auth = self.auth.auth
            response = await self.http_client.request(
                method, url, json=json, params=params, headers=headers, auth=auth, files=files
            )
        else:
            token = await self.bearer_token_manager.get()
            hdrs = headers or {}
            hdrs["Authorization"] = f"Bearer {token}"
            response = await self.http_client.request(method, url, json=json, params=params, headers=hdrs, files=files)

        if response.status_code == 429:
            reset_time = response.headers.get("x-rate-limit-reset")
            retry_after = float(reset_time or 0)
            raise RateLimitError(f"X rate limit hit. Body: {response.text}", platform="x", retry_after=retry_after)

        # Handle 401 for OAuth2 by invalidating token
        if response.status_code == 401 and current_strategy == "oauth2":
            self.bearer_token_manager.invalidate()

        response.raise_for_status()

        try:
            return response.json() if response.content else {}
        except Exception:
            return {}

    async def _paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        limit: int = 50,
        auth_type: str | None = None,
    ) -> PaginatedResult:
        """Handle X v2 pagination with next_token."""
        all_data = []
        p = params or {}
        # X v2 max results per page is typically 100 for most endpoints
        p["max_results"] = min(limit, 100)

        last_res = {}
        while len(all_data) < limit:
            res = await self._request("GET", path, params=p, auth_type=auth_type)
            last_res = res
            data = res.get("data", [])
            all_data.extend(data)

            meta = res.get("meta", {})
            next_token = meta.get("next_token")

            if not next_token or len(all_data) >= limit:
                break
            p["pagination_token"] = next_token

        return PaginatedResult(
            data=all_data[:limit],
            next_token=last_res.get("meta", {}).get("next_token"),
            result_count=len(all_data[:limit]),
        )
