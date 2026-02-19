"""
Social Media Connector SDK.
Unified API for Telegram, Slack, WhatsApp, Discord, Aratai, and Twitter.
"""
from collections.abc import Callable
from typing import Any

from socialconnector.core.exceptions import SocialConnectorError
from socialconnector.core.factory import AdapterFactory
from socialconnector.core.models import (
    Event,
    Media,
    Message,
    MessageResponse,
    UserInfo,
)
from socialconnector.core.registry import AdapterRegistry
from socialconnector.utils.http_client import HTTPClient


class SocialConnector:
    """Main entry point for the SDK."""

    def __init__(self, provider: str, **config: Any) -> None:
        """Initialize the connector with a specific provider and its config."""
        self.provider_name = provider

        # Initialize shared infrastructure
        timeout = config.get("timeout", 30.0)
        self._http_client = HTTPClient(timeout=timeout)

        # Use Factory to create adapter with DI
        self.adapter = AdapterFactory.create(
            provider=provider,
            http_client=self._http_client,
            **config
        )

    async def connect(self) -> None:
        """Establish connection to the platform."""
        await self.adapter.connect()

    async def disconnect(self) -> None:
        """Close platform connections and shared resources."""
        await self.adapter.disconnect()
        await self._http_client.close()

    async def post(
        self,
        text: str,
        *,
        media: list[Media] | None = None,
    ) -> MessageResponse:
        """Create a public post or status update."""
        return await self.adapter.post(text, media=media)

    async def direct_message(
        self,
        chat_id: str,
        text: str,
        *,
        reply_to: str | None = None,
    ) -> MessageResponse:
        """Send a direct message."""
        return await self.adapter.direct_message(chat_id, text, reply_to=reply_to)

    async def send_media(
        self,
        chat_id: str,
        media: Media,
        *,
        caption: str | None = None,
    ) -> MessageResponse:
        """Send a media attachment."""
        return await self.adapter.send_media(chat_id, media, caption=caption)

    def on_message(self, callback: Callable[[Message], Any]) -> Callable:
        """Decorator to register a message handler."""
        return self.adapter.on_message(callback)

    async def start(self) -> None:
        """Start polling or webhook processing."""
        await self.adapter.start_polling()


# Export key classes for easier access
__all__ = [
    "SocialConnector",
    "SocialConnectorError",
    "AdapterRegistry",
    "Message",
    "MessageResponse",
    "Event",
    "UserInfo",
    "Media",
]
