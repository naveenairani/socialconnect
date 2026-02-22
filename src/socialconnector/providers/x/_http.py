"""
X HTTP Mixin for unified request handling and pagination.
"""

import asyncio
import re
import time
from typing import Any
from urllib.parse import urlparse

from socialconnector.core.exceptions import RateLimitError, SocialConnectorError
from socialconnector.core.models import PaginatedResult


class XHttpMixin:
    """Mixin providing unified request and pagination logic for X API."""

    BASE_URL = "https://api.x.com/2"

    def _validate_path_param(self, name: str, value: str) -> str:
        """Validate path parameters against an allowlist."""
        if not value or not re.match(r"^[a-zA-Z0-9_-]+$", value):
            raise SocialConnectorError(f"Invalid path parameter {name}: {value}", platform="x")
        return value

    def _sanitize_url(self, url: str) -> str:
        """Strip whitespace and enforce https."""
        sanitized = url.strip()
        if not sanitized.startswith("https://"):
            raise SocialConnectorError(f"Insecure or invalid URL blocked: {sanitized}", platform="x")

        parsed = urlparse(sanitized)
        if parsed.netloc not in ("api.x.com", "api.twitter.com", "upload.twitter.com"):
            raise SocialConnectorError(f"SSRF blocked: unapproved domain {parsed.netloc}", platform="x")
        return sanitized

    # Minimum seconds between consecutive requests to avoid burst exhaustion.
    # X API v2 free tier: 1500 tweets/month ≈ conservative pacing.
    # Basic/Pro tiers: adjust as needed.
    MIN_REQUEST_INTERVAL = 1.0  # seconds
    MAX_RETRIES_ON_429 = 3

    async def _request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        files: dict[str, Any] | None = None,
        auth_type: str | None = None,  # "oauth1" or "oauth2"
    ) -> Any:
        """Unified request handler with auth dispatch and production rate-limit handling."""

        # ── 1. Enforce minimum spacing between requests ──
        if not hasattr(self, "_rate_limit_lock"):
            self._rate_limit_lock = asyncio.Lock()

        async with self._rate_limit_lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self.MIN_REQUEST_INTERVAL:
                delay = self.MIN_REQUEST_INTERVAL - elapsed
                await asyncio.sleep(delay)
            self._last_request_time = time.time()

        # ── 2. Proactive sleep if budget is exhausted or critically low ──
        if self._rate_limit_remaining is not None and self._rate_limit_remaining <= 0:
            reset_at = self._rate_limit_reset
            now = time.time()
            if now < reset_at:
                sleep_time = reset_at - now + 1
                self.logger.warning(
                    f"Rate limit exhausted — sleeping {sleep_time:.1f}s until window resets"
                )
                await asyncio.sleep(sleep_time)
                # Reset state after sleeping through the window
                self._rate_limit_remaining = None
        elif self._rate_limit_remaining is not None and self._rate_limit_remaining < 5:
            # Slow down when near the limit: spread remaining budget across time left
            reset_at = self._rate_limit_reset
            now = time.time()
            time_left = max(reset_at - now, 1)
            spacing = time_left / max(self._rate_limit_remaining, 1)
            if spacing > self.MIN_REQUEST_INTERVAL:
                self.logger.info(
                    f"Rate limit low ({self._rate_limit_remaining} left) — "
                    f"pacing requests every {spacing:.1f}s"
                )
                async with self._rate_limit_lock:
                    await asyncio.sleep(spacing)
                    self._last_request_time = time.time()

        # ── 3. Build and sanitize URL ──
        raw_url = path if path.startswith("http") else f"{self.BASE_URL.strip()}/{path.lstrip('/')}"
        url = self._sanitize_url(raw_url)

        # ── 4. Execute with 429 retry loop ──
        current_strategy = auth_type or self.auth_strategy
        response = None

        for attempt in range(1, self.MAX_RETRIES_ON_429 + 1):
            if current_strategy == "oauth1":
                auth = self.auth.auth
                response = await self.http_client.request(
                    method, url, data=data, json=json, params=params, headers=headers, auth=auth, files=files
                )
            else:
                token = await self.bearer_token_manager.get()
                hdrs = dict(headers) if headers else {}
                hdrs["Authorization"] = f"Bearer {token}"
                response = await self.http_client.request(
                    method, url, data=data, json=json, params=params, headers=hdrs, files=files
                )

            # ── 5. Update rate limit state from every response ──
            rem = response.headers.get("x-rate-limit-remaining")
            res = response.headers.get("x-rate-limit-reset")
            if rem is not None:
                self._rate_limit_remaining = int(rem)
            if res is not None:
                self._rate_limit_reset = float(res)

            # ── 6. Handle 429 with automatic retry + backoff ──
            if response.status_code == 429:
                if attempt < self.MAX_RETRIES_ON_429:
                    reset_time = self._rate_limit_reset
                    now = time.time()
                    # Use reset header if available, otherwise exponential backoff
                    wait = reset_time - now + 1 if reset_time > now else min(2**attempt, 60)  # 2s, 4s, capped at 60s
                    self.logger.warning(
                        f"429 Rate limited (attempt {attempt}/{self.MAX_RETRIES_ON_429}) "
                        f"— retrying in {wait:.1f}s"
                    )
                    await asyncio.sleep(wait)
                    self._rate_limit_remaining = None  # Reset so we don't double-sleep
                    continue
                else:
                    raise RateLimitError(
                        "X rate limit hit after all retries exhausted.",
                        platform="x",
                        retry_after=self._rate_limit_reset,
                    )

            break  # Non-429 response, exit retry loop

        # ── 7. Handle 401 for OAuth2 by invalidating token ──
        if response.status_code == 401 and current_strategy == "oauth2":
            self.bearer_token_manager.invalidate()

        try:
            response.raise_for_status()
        except Exception as e:
            msg = f"X API request failed with status {response.status_code}"
            raise SocialConnectorError(msg, platform="x", original_error=e) from e

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
