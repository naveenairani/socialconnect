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


class StreamResponse(BaseModel):
    """Raw data yielded from a streaming endpoint."""
    data: dict[str, Any] | None = None
    includes: dict[str, Any] | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


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


class UpdateSubscriptionRequest(BaseModel):
    """Request model for update_subscription"""
    model_config = ConfigDict(populate_by_name=True)


class UpdateSubscriptionResponseData(BaseModel):
    """Nested model for UpdateSubscriptionResponseData"""
    subscribed: bool | None = None


class UpdateSubscriptionResponse(BaseModel):
    """Response model for update_subscription"""
    data: UpdateSubscriptionResponseData | None = None
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
    meta: "PageInfo | None" = None

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
    create_replay_job_response: "CreateReplayJobResponse | None" = None
    delete_subscription_response: "DeleteSubscriptionResponse | None" = None
    get_subscription_count_response: "GetSubscriptionCountResponse | None" = None


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


# --- X Communities API Models ---

class GetByIdResponseData(BaseModel):
    created_at: str | None = None
    id: str | None = None
    name: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetByIdResponse(BaseModel):
    data: GetByIdResponseData | dict[str, Any] = Field(
        description="A X Community is a curated group of Posts.", default_factory=dict
    )
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class SearchResponseMeta(BaseModel):
    next_token: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class SearchResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: SearchResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


# --- X Compliance API Models ---

class ComplianceJobData(BaseModel):
    created_at: str | None = None
    download_expires_at: str | None = None
    download_url: str | None = None
    id: str | None = None
    name: str | None = None
    status: str | None = None
    type: str | None = None
    upload_expires_at: str | None = None
    upload_url: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetJobsByIdResponse(BaseModel):
    data: ComplianceJobData = Field(default_factory=dict)
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetJobsResponseMeta(BaseModel):
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetJobsResponse(BaseModel):
    data: list[ComplianceJobData] | None = None
    errors: list[Any] | None = None
    meta: GetJobsResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CreateJobsRequest(BaseModel):
    type: str = Field(..., description="Type of compliance job.")
    name: str | None = None
    resumable: bool | None = None

    model_config = ConfigDict(populate_by_name=True)


class CreateJobsResponse(BaseModel):
    data: ComplianceJobData = Field(default_factory=dict)
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


# --- X Connections API Models ---

class DeleteAllResponseData(BaseModel):
    failed_kills: int | None = None
    results: list[Any] | None = None
    successful_kills: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class DeleteAllResponse(BaseModel):
    data: DeleteAllResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetConnectionHistoryResponseMeta(BaseModel):
    next_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetConnectionHistoryResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: GetConnectionHistoryResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class DeleteByUuidsRequest(BaseModel):
    uuids: list[str] = Field(..., description="Array of connection UUIDs to terminate")

    model_config = ConfigDict(populate_by_name=True)


class DeleteByUuidsResponseData(BaseModel):
    failed_kills: int | None = None
    results: list[Any] | None = None
    successful_kills: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class DeleteByUuidsResponse(BaseModel):
    data: DeleteByUuidsResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class DeleteByEndpointResponseData(BaseModel):
    failed_kills: int | None = None
    results: list[Any] | None = None
    successful_kills: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class DeleteByEndpointResponse(BaseModel):
    data: DeleteByEndpointResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


# --- X Direct Messages API Models ---

class GetEventsByParticipantIdResponseIncludes(BaseModel):
    media: list[Any] | None = None
    places: list[Any] | None = None
    polls: list[Any] | None = None
    topics: list[Any] | None = None
    tweets: list[Any] | None = None
    users: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetEventsByParticipantIdResponseMeta(BaseModel):
    next_token: str | None = None
    previous_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetEventsByParticipantIdResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    includes: Any | None = None
    meta: GetEventsByParticipantIdResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetEventsByConversationIdResponseIncludes(BaseModel):
    media: list[Any] | None = None
    places: list[Any] | None = None
    polls: list[Any] | None = None
    topics: list[Any] | None = None
    tweets: list[Any] | None = None
    users: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetEventsByConversationIdResponseMeta(BaseModel):
    next_token: str | None = None
    previous_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetEventsByConversationIdResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    includes: Any | None = None
    meta: GetEventsByConversationIdResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetEventsByIdResponseDataAttachments(BaseModel):
    card_ids: list[Any] | None = None
    media_keys: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetEventsByIdResponseData(BaseModel):
    attachments: GetEventsByIdResponseDataAttachments | None = None
    cashtags: list[Any] | None = None
    created_at: str | None = None
    dm_conversation_id: str | None = None
    event_type: str | None = None
    hashtags: list[Any] | None = None
    id: str | None = None
    mentions: list[Any] | None = None
    participant_ids: list[Any] | None = None
    referenced_tweets: list[Any] | None = None
    sender_id: str | None = None
    text: str | None = None
    urls: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetEventsByIdResponseIncludes(BaseModel):
    media: list[Any] | None = None
    places: list[Any] | None = None
    polls: list[Any] | None = None
    topics: list[Any] | None = None
    tweets: list[Any] | None = None
    users: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetEventsByIdResponse(BaseModel):
    data: GetEventsByIdResponseData | None = Field(default_factory=dict)
    errors: list[Any] | None = None
    includes: Any | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class DeleteEventsResponseData(BaseModel):
    deleted: bool | None = None

    model_config = ConfigDict(populate_by_name=True)


class DeleteEventsResponse(BaseModel):
    data: DeleteEventsResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CreateConversationRequest(BaseModel):
    conversation_type: str = Field(..., description="The conversation type that is being created.")
    message: str = Field(...)
    participant_ids: str = Field(..., description="Participants for the DM Conversation.")

    model_config = ConfigDict(populate_by_name=True)


class CreateConversationResponseData(BaseModel):
    dm_conversation_id: str | None = None
    dm_event_id: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class CreateConversationResponse(BaseModel):
    data: CreateConversationResponseData | None = Field(default_factory=dict)
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CreateByConversationIdRequest(BaseModel):
    attachments: list[Any] | None = Field(default=None, description="Attachments to a DM Event.")
    text: str | None = Field(default=None, description="Text of the message.")

    model_config = ConfigDict(populate_by_name=True)


class CreateByConversationIdResponseData(BaseModel):
    dm_conversation_id: str | None = None
    dm_event_id: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class CreateByConversationIdResponse(BaseModel):
    data: CreateByConversationIdResponseData | None = Field(default_factory=dict)
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CreateByParticipantIdRequest(BaseModel):
    attachments: list[Any] | None = Field(default=None, description="Attachments to a DM Event.")
    text: str | None = Field(default=None, description="Text of the message.")

    model_config = ConfigDict(populate_by_name=True)


class CreateByParticipantIdResponseData(BaseModel):
    dm_conversation_id: str | None = None
    dm_event_id: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class CreateByParticipantIdResponse(BaseModel):
    data: CreateByParticipantIdResponseData | None = Field(default_factory=dict)
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetEventsResponseIncludes(BaseModel):
    media: list[Any] | None = None
    places: list[Any] | None = None
    polls: list[Any] | None = None
    topics: list[Any] | None = None
    tweets: list[Any] | None = None
    users: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetEventsResponseMeta(BaseModel):
    next_token: str | None = None
    previous_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetEventsResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    includes: Any | None = None
    meta: GetEventsResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


# --- X Chat API Models ---

class SendMessageRequest(BaseModel):
    """Request model for send_message"""
    encoded_message_create_event: str
    message_id: str
    conversation_token: str | None = None
    encoded_message_event_signature: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class SendMessageResponseData(BaseModel):
    encoded_message_event: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class SendMessageResponse(BaseModel):
    data: SendMessageResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetConversationResponseMeta(BaseModel):
    has_more: bool | None = None
    missing_conversation_key_change_events: list[Any] | None = None
    next_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetConversationResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: GetConversationResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetUserPublicKeysResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class AddUserPublicKeyRequestPublicKey(BaseModel):
    identity_public_key_signature: str | None = None
    public_key: str | None = None
    public_key_fingerprint: str | None = None
    registration_method: str | None = None
    signing_public_key: str | None = None
    signing_public_key_signature: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class AddUserPublicKeyRequest(BaseModel):
    public_key: str
    version: str
    generate_version: bool | None = None

    model_config = ConfigDict(populate_by_name=True)


class AddUserPublicKeyResponseDataTokenMap(BaseModel):
    key_store_token_map_json: str | None = None
    max_guess_count: int | None = None
    realm_state_string: str | None = None
    recover_threshold: int | None = None
    register_threshold: int | None = None
    token_map: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class AddUserPublicKeyResponseData(BaseModel):
    error_code: str | None = None
    token_map: AddUserPublicKeyResponseDataTokenMap | None = None
    version: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class AddUserPublicKeyResponse(BaseModel):
    data: AddUserPublicKeyResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetConversationsResponseIncludes(BaseModel):
    users: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetConversationsResponseMeta(BaseModel):
    has_message_requests: bool | None = None
    next_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetConversationsResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    includes: GetConversationsResponseIncludes | None = None
    meta: GetConversationsResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


