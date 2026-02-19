from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class MediaType(str, Enum):
    """Supported media types."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    STICKER = "sticker"
    VOICE = "voice"
    ANIMATION = "animation"


class EventType(str, Enum):
    """Supported event types."""
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_EDITED = "message_edited"
    MESSAGE_DELETED = "message_deleted"
    REACTION_ADDED = "reaction_added"
    REACTION_REMOVED = "reaction_removed"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    TYPING = "typing"
    CUSTOM = "custom"


class AdapterConfig(BaseModel):
    """Configuration for initializing a provider adapter."""
    provider: str
    api_key: str
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    timeout: float = 30.0
    max_retries: int = 3
    rate_limit: Optional[float] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class UserInfo(BaseModel):
    """Unified user information."""
    id: str
    platform: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_bot: bool = False
    raw: dict[str, Any] = Field(default_factory=dict)


class Media(BaseModel):
    """Unified media attachment."""
    type: MediaType
    url: Optional[str] = None
    file_bytes: Optional[bytes] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """A unified message received from any platform."""
    model_config = ConfigDict(frozen=True)

    id: str
    platform: str
    chat_id: str
    sender: UserInfo
    text: Optional[str] = None
    media: list[Media] = Field(default_factory=list)
    reply_to_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    raw: dict[str, Any] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    """Response after sending a message."""
    success: bool
    message_id: Optional[str] = None
    platform: str
    timestamp: datetime = Field(default_factory=datetime.now)
    raw: dict[str, Any] = Field(default_factory=dict)


class WebhookConfig(BaseModel):
    """Webhook registration configuration."""
    url: str
    secret: Optional[str] = None
    events: list[str] = Field(default_factory=lambda: ["*"])


class HealthStatus(BaseModel):
    """Result of a provider health check."""
    provider: str
    healthy: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.now)


class Event(BaseModel):
    """Unified event from any platform."""
    type: EventType
    platform: str
    chat_id: Optional[str] = None
    user: Optional[UserInfo] = None
    message: Optional[Message] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    raw: dict[str, Any] = Field(default_factory=dict)
