from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    api_secret: str | None = None
    base_url: str | None = None
    timeout: float = 30.0
    max_retries: int = 3
    rate_limit: float | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider", "api_key")
    @classmethod
    def name_must_be_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v


class UserInfo(BaseModel):
    """Unified user information."""

    id: str
    platform: str
    username: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    is_bot: bool = False
    raw: dict[str, Any] = Field(default_factory=dict)


class Media(BaseModel):
    """Unified media attachment."""

    type: MediaType
    url: str | None = None
    file_bytes: bytes | None = None
    file_name: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """A unified message received from any platform."""

    model_config = ConfigDict(frozen=True)

    id: str
    platform: str
    chat_id: str
    sender: UserInfo
    text: str | None = None
    media: list[Media] = Field(default_factory=list)
    reply_to_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    raw: dict[str, Any] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    """Response after sending a message."""

    success: bool
    message_id: str | None = None
    platform: str
    timestamp: datetime = Field(default_factory=datetime.now)
    raw: dict[str, Any] = Field(default_factory=dict)


class WebhookConfig(BaseModel):
    """Webhook registration configuration."""

    url: str
    secret: str | None = None
    events: list[str] = Field(default_factory=lambda: ["*"])


class HealthStatus(BaseModel):
    """Result of a provider health check."""

    provider: str
    healthy: bool
    latency_ms: float | None = None
    error: str | None = None
    checked_at: datetime = Field(default_factory=datetime.now)


class Event(BaseModel):
    """Unified event from any platform."""

    type: EventType
    platform: str
    chat_id: str | None = None
    user: UserInfo | None = None
    message: Message | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    raw: dict[str, Any] = Field(default_factory=dict)


class Tweet(BaseModel):
    """A single tweet/post from X."""

    id: str
    text: str
    author_id: str | None = None
    created_at: datetime | None = None
    conversation_id: str | None = None
    in_reply_to_user_id: str | None = None
    referenced_tweets: list[dict[str, Any]] = Field(default_factory=list)
    public_metrics: dict[str, int] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)


class CommunityNote(BaseModel):
    """Unified Community Note model."""


    id: str
    text: str | None = None
    note_id: str | None = None
    created_at: datetime | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class EvaluateRequest(BaseModel):
    """Request to evaluate a community note."""

    note_id: str
    helpful: bool | None = None
    rating: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class EvaluateResponse(BaseModel):
    """Response from evaluating a community note."""

    success: bool
    raw: dict[str, Any] = Field(default_factory=dict)


class DeleteResponse(BaseModel):
    """Response from a delete operation."""

    success: bool
    raw: dict[str, Any] = Field(default_factory=dict)




class DMConversation(BaseModel):
    """A direct message thread."""

    id: str
    platform: str
    participant_ids: list[str] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)


class StreamRule(BaseModel):
    """A filtered stream rule."""

    id: str | None = None
    value: str
    tag: str | None = None


class PaginatedResult(BaseModel):
    """Wrapper for paginated API responses."""

    data: list[Any] = Field(default_factory=list)
    next_token: str | None = None
    result_count: int = 0


class PageInfo(BaseModel):
    """Pagination metadata returned alongside a page of results."""

    next_token: str | None = None
    previous_token: str | None = None
    result_count: int = 0
    total_results: int | None = None
    newest_id: str | None = None
    oldest_id: str | None = None


# X Account Activity Models

class ValidateSubscriptionResponseData(BaseModel):
    """Nested model for ValidateSubscriptionResponseData"""
    subscribed: bool | None = None

class ValidateSubscriptionResponse(BaseModel):
    """Response model for validate_subscription"""
    data: ValidateSubscriptionResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CreateSubscriptionRequest(BaseModel):
    """Request model for create_subscription"""
    model_config = ConfigDict(populate_by_name=True)


class CreateSubscriptionResponseData(BaseModel):
    """Nested model for CreateSubscriptionResponseData"""
    subscribed: bool | None = None


class CreateSubscriptionResponse(BaseModel):
    """Response model for create_subscription"""
    data: CreateSubscriptionResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetSubscriptionsResponseData(BaseModel):
    """Nested model for GetSubscriptionsResponseData"""
    application_id: str | None = None
    subscriptions: list[Any] | None = None
    webhook_id: str | None = None
    webhook_url: str | None = None


class GetSubscriptionsResponse(BaseModel):
    """Response model for get_subscriptions"""
    data: GetSubscriptionsResponseData = Field(
        description="The list of active subscriptions for a specified webhook",
        default_factory=lambda: GetSubscriptionsResponseData(),
    )
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class DeleteSubscriptionResponseData(BaseModel):
    """Nested model for DeleteSubscriptionResponseData"""
    subscribed: bool | None = None


class DeleteSubscriptionResponse(BaseModel):
    """Response model for delete_subscription"""
    data: DeleteSubscriptionResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetSubscriptionCountResponseData(BaseModel):
    """Nested model for GetSubscriptionCountResponseData"""
    account_name: str | None = None
    provisioned_count: str | None = None
    subscriptions_count_all: str | None = None
    subscriptions_count_direct_messages: str | None = None


class GetSubscriptionCountResponse(BaseModel):
    """Response model for get_subscription_count"""
    data: GetSubscriptionCountResponseData = Field(
        description="The count of active subscriptions across all webhooks",
        default_factory=lambda: GetSubscriptionCountResponseData(),
    )
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CreateReplayJobResponse(BaseModel):
    """Response model for create_replay_job"""
    created_at: str | None = None
    job_id: str | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")
