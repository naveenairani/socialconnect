from typing import Any

from pydantic import BaseModel, ConfigDict


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
