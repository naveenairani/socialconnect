"""
X Chat API Mixin for encrypted direct messages and public keys.
"""

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from socialconnector.core.models import (
    AddUserPublicKeyRequest,
    AddUserPublicKeyResponse,
    GetConversationResponse,
    GetConversationsResponse,
    GetUserPublicKeysResponse,
    SendMessageRequest,
    SendMessageResponse,
)

if TYPE_CHECKING:
    import logging

    class XChatMixinProtocol:
        logger: logging.Logger
        http_client: Any
        bearer_token_manager: Any
        auth_strategy: str
        auth: Any
        config: Any
        BASE_URL: str
        _request: Any
        _paginate: Any
        _emit: Any
        _validate_path_param: Any
        _get_oauth2_user_token: Any
        _invalidate_oauth2_user_token: Any
else:
    class XChatMixinProtocol:
        pass


class XChatMixin(XChatMixinProtocol):
    """Mixin for X Chat API operations (encrypted DMs, public keys)."""

    async def send_message(
        self, conversation_id: str, body: SendMessageRequest
    ) -> SendMessageResponse:
        """
        Send Chat Message
        Sends an encrypted message to a specific Chat conversation.
        """
        conv = self._validate_path_param("conversation_id", conversation_id)
        path = f"chat/conversations/{conv}/messages"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("POST", path, json=json_data, auth_type="oauth1")
        return SendMessageResponse.model_validate(res)

    async def get_conversation(
        self,
        conversation_id: str,
        max_results: int | None = None,
        pagination_token: str | None = None,
        chat_message_event_fields: list[str] | None = None,
    ) -> AsyncIterator[GetConversationResponse]:
        """
        Get Chat Conversation
        Retrieves messages and key change events for a specific Chat conversation with pagination support.
        """
        conv = self._validate_path_param("conversation_id", conversation_id)
        path = f"chat/conversations/{conv}"

        current_token = pagination_token
        while True:
            params: dict[str, Any] = {}
            if max_results is not None:
                params["max_results"] = max_results
            if chat_message_event_fields is not None:
                params["chat_message_event.fields"] = ",".join(chat_message_event_fields)
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", path, params=params, auth_type="oauth1")
            page_res = GetConversationResponse.model_validate(res)
            yield page_res

            next_token = None
            if page_res.meta and page_res.meta.next_token:
                next_token = page_res.meta.next_token

            if not next_token:
                break
            current_token = next_token

    async def get_user_public_keys(
        self, user_id: str, public_key_fields: list[str] | None = None
    ) -> GetUserPublicKeysResponse:
        """
        Get user public keys
        Returns the public keys and Juicebox configuration for the specified user.
        """
        uid = self._validate_path_param("user_id", user_id)
        path = f"users/{uid}/public_keys"
        params: dict[str, Any] = {}
        if public_key_fields is not None:
            params["public_key.fields"] = ",".join(public_key_fields)

        res = await self._request("GET", path, params=params, auth_type="oauth1")
        return GetUserPublicKeysResponse.model_validate(res)

    async def add_user_public_key(
        self, user_id: str, body: AddUserPublicKeyRequest
    ) -> AddUserPublicKeyResponse:
        """
        Add public key
        Registers a user's public key for X Chat encryption.
        """
        uid = self._validate_path_param("user_id", user_id)
        path = f"users/{uid}/public_keys"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("POST", path, json=json_data, auth_type="oauth1")
        return AddUserPublicKeyResponse.model_validate(res)

    async def get_conversations(
        self,
        max_results: int | None = None,
        pagination_token: str | None = None,
        chat_conversation_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        user_fields: list[str] | None = None,
    ) -> AsyncIterator[GetConversationsResponse]:
        """
        Get Chat Conversations
        Retrieves a list of Chat conversations for the authenticated user's inbox.
        """
        path = "chat/conversations"

        current_token = pagination_token
        while True:
            params: dict[str, Any] = {}
            if max_results is not None:
                params["max_results"] = max_results
            if chat_conversation_fields is not None:
                params["chat_conversation.fields"] = ",".join(chat_conversation_fields)
            if expansions is not None:
                params["expansions"] = ",".join(expansions)
            if user_fields is not None:
                params["user.fields"] = ",".join(user_fields)
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", path, params=params, auth_type="oauth1")
            page_res = GetConversationsResponse.model_validate(res)
            yield page_res

            next_token = None
            if page_res.meta and page_res.meta.next_token:
                next_token = page_res.meta.next_token

            if not next_token:
                break
            current_token = next_token
