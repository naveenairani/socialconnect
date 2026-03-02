"""
Social Media Connector SDK.
Unified API for Telegram, Slack, WhatsApp, Discord, Aratai, and Twitter.
"""

from typing import Any, Literal, overload

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
from socialconnector.providers.x.adapter import XAdapter
from socialconnector.utils.http_client import HTTPClient


@overload
def SocialConnector(provider: Literal["x", "twitter"], **config: Any) -> XAdapter: ... # noqa: N802

@overload
def SocialConnector(provider: str, **config: Any) -> Any: ... # noqa: N802

def SocialConnector(provider: str, **config: Any) -> Any: # noqa: N802
    """
    Main entry point for the SDK.
    Returns a strongly-typed adapter instance for the specified provider.
    """
    timeout = config.get("timeout", 30.0)
    http_client = HTTPClient(timeout=timeout)

    return AdapterFactory.create(provider=provider, http_client=http_client, **config)


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
