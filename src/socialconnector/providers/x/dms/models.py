from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
    data: GetEventsByIdResponseData | None = None
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
    data: CreateConversationResponseData | None = None
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
    data: CreateByConversationIdResponseData | None = None
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
    data: CreateByParticipantIdResponseData | None = None
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
