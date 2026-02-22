"""
X Stream Mixin for managing filtered stream rules and polling.
"""

import asyncio

from socialconnector.core.models import StreamRule
from socialconnector.core.streaming import StreamConfig, StreamError, stream_with_retry


class XStreamMixin:
    """Mixin for filtered stream operations (rules, start/stop polling)."""

    _stream_active: bool = False

    async def add_stream_rule(self, value: str, tag: str | None = None) -> list[StreamRule]:
        """Add a rule to the filtered stream."""
        path = "tweets/search/stream/rules"
        data = {"add": [{"value": value, "tag": tag} if tag else {"value": value}]}
        res = await self._request("POST", path, json=data, auth_type="oauth2")
        rules = res.get("data", [])
        return [StreamRule(id=r.get("id"), value=r.get("value"), tag=r.get("tag")) for r in rules]

    async def delete_stream_rules(self, ids: list[str]) -> bool:
        """Delete rules from the filtered stream."""
        path = "tweets/search/stream/rules"
        data = {"delete": {"ids": ids}}
        res = await self._request("POST", path, json=data, auth_type="oauth2")
        return "deleted" in res.get("meta", {}).get("summary", {})

    async def get_stream_rules(self) -> list[StreamRule]:
        """Get all filtered stream rules."""
        path = "tweets/search/stream/rules"
        res = await self._request("GET", path, auth_type="oauth2")
        rules = res.get("data", [])
        return [StreamRule(id=r.get("id"), value=r.get("value"), tag=r.get("tag")) for r in rules]

    async def start_polling(self) -> None:
        """Start filtered stream polling (NDJSON, with automatic reconnection).

        Emits a ``"tweet_received"`` event for each incoming tweet.
        Streams until ``stop_polling()`` is called.
        """
        self._stream_active = True
        self.logger.info("Starting X filtered stream…")

        bearer_token = await self.bearer_token_manager.get()
        headers = {"Authorization": f"Bearer {bearer_token}"}
        url = f"{self.config.base_url or 'https://api.x.com'}/2/tweets/search/stream"
        params = {
            "tweet.fields": "id,text,author_id,created_at,conversation_id",
            "expansions": "author_id",
        }

        def _on_connect() -> None:
            self.logger.info("X stream connected.")

        def _on_reconnect(attempt: int, delay: float) -> None:
            self.logger.warning("X stream reconnecting in %.1fs (attempt %d)…", delay, attempt)

        config = StreamConfig(
            max_retries=self.config.max_retries,
            on_connect=_on_connect,
            on_reconnect=_on_reconnect,
        )

        try:
            iterator = stream_with_retry(
                self.http_client,
                "GET",
                url,
                params=params,
                headers=headers,
                config=config,
            )
            while self._stream_active:
                try:
                    event = await asyncio.wait_for(anext(iterator), timeout=2.0)
                    await self._emit("tweet_received", event)
                except asyncio.TimeoutError:
                    continue
                except StopAsyncIteration:
                    break
        except StreamError as exc:
            self.logger.error("X stream terminated: %s", exc)
            raise

    async def stop_polling(self) -> None:
        """Stop filtered stream polling."""
        self._stream_active = False
        self.logger.info("X stream polling stopped.")
