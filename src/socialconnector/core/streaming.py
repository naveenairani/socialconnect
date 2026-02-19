"""
Provider-agnostic async streaming with exponential backoff and retry.

Inspired by X SDK patterns, adapted for httpx.AsyncClient and the
socialconnector architecture.

Usage in any provider mixin::

    config = StreamConfig(max_retries=10, on_connect=lambda: print("connected"))
    async for data in self.stream_with_retry("GET", url, config=config):
        await self._emit("message_received", data)
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import random
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class StreamErrorType(Enum):
    """Classification of streaming errors for retry decisions."""

    CONNECTION_ERROR = "connection_error"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    RATE_LIMITED = "rate_limited"
    STREAM_INTERRUPTED = "stream_interrupted"
    AUTH_ERROR = "authentication_error"
    CLIENT_ERROR = "client_error"
    FATAL = "fatal"


class StreamError(Exception):
    """Streaming error with retryability classification."""

    def __init__(
        self,
        message: str,
        error_type: StreamErrorType,
        original: Exception | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.original = original
        self.status_code = status_code

    @property
    def is_retryable(self) -> bool:
        return self.error_type in {
            StreamErrorType.CONNECTION_ERROR,
            StreamErrorType.TIMEOUT,
            StreamErrorType.SERVER_ERROR,
            StreamErrorType.RATE_LIMITED,
            StreamErrorType.STREAM_INTERRUPTED,
        }


@dataclass
class StreamConfig:
    """Configuration for streaming connections.

    Attributes:
        max_retries: Max reconnection attempts. ``-1`` for unlimited.
        initial_backoff: Starting backoff in seconds.
        max_backoff: Backoff cap in seconds.
        backoff_multiplier: Exponential multiplier.
        jitter: Whether to add random jitter (recommended).
        timeout: HTTP request timeout in seconds (``None`` = no timeout).
        on_connect: Callback fired on successful connection.
        on_disconnect: Callback fired when connection drops.
        on_reconnect: Callback fired before each retry (attempt, delay).
        on_error: Callback fired when a ``StreamError`` occurs.
    """

    max_retries: int = 10
    initial_backoff: float = 1.0
    max_backoff: float = 64.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    timeout: float | None = None
    on_connect: Callable[[], None] | None = None
    on_disconnect: Callable[[Exception | None], None] | None = None
    on_reconnect: Callable[[int, float], None] | None = None
    on_error: Callable[[StreamError], None] | None = None


def _compute_backoff(
    attempt: int,
    initial: float,
    maximum: float,
    multiplier: float,
    jitter: bool,
) -> float:
    delay = min(initial * (multiplier**attempt), maximum)
    if jitter:
        delay += delay * random.uniform(0, 0.25)
    return delay


def _classify(exc: Exception, status: int | None = None) -> StreamError:
    """Convert a raw exception into a classified ``StreamError``."""
    if status is not None:
        if status == 429:
            return StreamError("Rate limited (429)", StreamErrorType.RATE_LIMITED, exc, status)
        if status in (401, 403):
            return StreamError(f"Auth error ({status})", StreamErrorType.AUTH_ERROR, exc, status)
        if 400 <= status < 500:
            return StreamError(f"Client error ({status})", StreamErrorType.CLIENT_ERROR, exc, status)
        if status >= 500:
            return StreamError(f"Server error ({status})", StreamErrorType.SERVER_ERROR, exc, status)
    if isinstance(exc, httpx.TimeoutException):
        return StreamError(f"Timeout: {exc}", StreamErrorType.TIMEOUT, exc)
    if isinstance(exc, (httpx.ConnectError, httpx.RemoteProtocolError)):
        return StreamError(f"Connection error: {exc}", StreamErrorType.CONNECTION_ERROR, exc)
    if isinstance(exc, httpx.StreamError):
        return StreamError(f"Stream interrupted: {exc}", StreamErrorType.STREAM_INTERRUPTED, exc)
    return StreamError(f"Unexpected: {exc}", StreamErrorType.FATAL, exc)


async def stream_with_retry(
    http_client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    config: StreamConfig | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """
    Async generator that streams NDJSON from a URL with automatic retry.

    Yields parsed JSON objects. Handles reconnection transparently.

    Args:
        http_client: The shared ``httpx.AsyncClient`` from the adapter.
        method: HTTP verb (``"GET"`` for most streaming endpoints).
        url: Full streaming endpoint URL.
        params: Optional query parameters.
        headers: Optional additional headers (auth headers etc).
        config: ``StreamConfig`` with retry/callback settings.
    """
    cfg = config or StreamConfig()
    attempt = 0

    while True:
        try:
            async with http_client.stream(
                method,
                url,
                params=params,
                headers=headers,
                timeout=cfg.timeout,
            ) as response:
                if response.status_code != 200:
                    await response.aread()
                    raise _classify(
                        httpx.HTTPStatusError(
                            f"HTTP {response.status_code}",
                            request=response.request,
                            response=response,
                        ),
                        response.status_code,
                    )

                # Connected successfully
                attempt = 0
                if cfg.on_connect:
                    with contextlib.suppress(Exception):
                        cfg.on_connect()

                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line or line in ("{}", ""):
                            continue
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            logger.debug("Skipping bad JSON: %s", line[:80])

            # Server closed the connection normally — reconnect
            if cfg.on_disconnect:
                with contextlib.suppress(Exception):
                    cfg.on_disconnect(None)

        except StreamError as exc:
            if cfg.on_error:
                with contextlib.suppress(Exception):
                    cfg.on_error(exc)
            if cfg.on_disconnect:
                with contextlib.suppress(Exception):
                    cfg.on_disconnect(exc.original)
            if not exc.is_retryable:
                raise
            if cfg.max_retries >= 0 and attempt >= cfg.max_retries:
                raise StreamError(
                    f"Max retries ({cfg.max_retries}) exceeded",
                    StreamErrorType.FATAL,
                    exc.original,
                ) from exc.original
            delay = _compute_backoff(
                attempt,
                cfg.initial_backoff,
                cfg.max_backoff,
                cfg.backoff_multiplier,
                cfg.jitter,
            )
            attempt += 1
            logger.info("Stream reconnecting in %.2fs (attempt %d)…", delay, attempt)
            if cfg.on_reconnect:
                with contextlib.suppress(Exception):
                    cfg.on_reconnect(attempt, delay)
            await asyncio.sleep(delay)

        except Exception as exc:
            stream_exc = _classify(exc)
            if not stream_exc.is_retryable:
                raise stream_exc from exc
            if cfg.max_retries >= 0 and attempt >= cfg.max_retries:
                raise StreamError(
                    "Max retries exceeded",
                    StreamErrorType.FATAL,
                    exc,
                ) from exc
            delay = _compute_backoff(
                attempt,
                cfg.initial_backoff,
                cfg.max_backoff,
                cfg.backoff_multiplier,
                cfg.jitter,
            )
            attempt += 1
            await asyncio.sleep(delay)
