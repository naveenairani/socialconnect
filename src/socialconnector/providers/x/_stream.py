"""
X Stream Mixin for managing filtered stream rules and polling.
"""

from socialconnector.core.models import StreamRule


class XStreamMixin:
    """Mixin for filtered stream operations (rules, start/stop polling)."""

    async def add_stream_rule(self, value: str, tag: str | None = None) -> list[StreamRule]:
        """Add a rule to the filtered stream."""
        path = "tweets/search/stream/rules"
        data = {"add": [{"value": value, "tag": tag} if tag else {"value": value}]}
        res = await self._request("POST", path, json=data, auth_type="oauth2")
        data = res.get("data", [])
        return [StreamRule(id=r.get("id"), value=r.get("value"), tag=r.get("tag")) for r in data]

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
        data = res.get("data", [])
        return [StreamRule(id=r.get("id"), value=r.get("value"), tag=r.get("tag")) for r in data]

    async def start_polling(self) -> None:
        """Start filtered stream polling."""
        self.logger.info("Starting X filtered stream polling...")
        # Note: Real SSE stream implementation requires a persistent connection runner.

    async def stop_polling(self) -> None:
        """Stop filtered stream polling."""
        self.logger.info("Stopping X filtered stream polling...")
