"""
X Direct Messages Mixin for managing conversations and messages.
"""

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from socialconnector.core.models import (
    CreateByConversationIdRequest,
    CreateByConversationIdResponse,
    CreateByParticipantIdRequest,
    CreateByParticipantIdResponse,
    CreateConversationRequest,
    CreateConversationResponse,
    DeleteEventsResponse,
    GetEventsByConversationIdResponse,
    GetEventsByIdResponse,
    GetEventsByParticipantIdResponse,
    GetEventsResponse,
    Message,
    MessageResponse,
    UserInfo,
)


class XDmsMixin:
    """Mixin for direct message operations (with user, in conversation, lookup)."""

    async def direct_message(
        self,
        chat_id: str,
        text: str,
        *,
        reply_to: str | None = None,
    ) -> MessageResponse:
        """
        Send a direct message to a user.

        Note: chat_id is treated as a recipient user ID. Always routes to
        /2/dm_conversations/with/:recipient_id/messages.
        """
        path = f"dm_conversations/with/{self._validate_path_param('chat_id', chat_id)}/messages"
        data = {"text": text}
        res = await self._request("POST", path, json=data, auth_type="oauth1")

        dm_data = res.get("data", {})
        return MessageResponse(
            success=True, message_id=dm_data.get("dm_id") or dm_data.get("id"), platform="x", raw=res
        )

    async def send_to_conversation(self, conversation_id: str, text: str) -> MessageResponse:
        """
        Send a direct message to an existing conversation.
        """
        path = f"dm_conversations/{self._validate_path_param('conversation_id', conversation_id)}/messages"
        data = {"text": text}
        res = await self._request("POST", path, json=data, auth_type="oauth1")

        dm_data = res.get("data", {})
        return MessageResponse(
            success=True, message_id=dm_data.get("dm_id") or dm_data.get("id"), platform="x", raw=res
        )

    async def get_messages(self, chat_id: str | None = None, *, limit: int = 50) -> list[Message]:
        """Get DM events. If chat_id is provided, filters for that conversation."""
        if chat_id:
            return await self.get_conversation_messages(chat_id, limit=limit)

        path = "dm_events"
        params = {"dm_event.fields": "id,text,sender_id,created_at,dm_conversation_id,event_type,participant_ids"}

        # Fix Bug #4: pass auth_type="oauth1"
        res = await self._paginate(path, params, limit=limit, auth_type="oauth1")

        return self._convert_dm_events(res.data)

    async def get_conversation_messages(self, conversation_id: str, *, limit: int = 50) -> list[Message]:
        """Get DM events for a specific conversation ID."""
        path = f"dm_conversations/{self._validate_path_param('conversation_id', conversation_id)}/dm_events"
        params = {"dm_event.fields": "id,text,sender_id,created_at,dm_conversation_id,event_type,participant_ids"}
        res = await self._paginate(path, params, limit=limit, auth_type="oauth1")
        return self._convert_dm_events(res.data)

    async def get_participant_messages(self, participant_id: str, *, limit: int = 50) -> list[Message]:
        """Get DM events for a one-to-one conversation with a participant."""
        path = f"dm_conversations/with/{self._validate_path_param('participant_id', participant_id)}/dm_events"
        params = {"dm_event.fields": "id,text,sender_id,created_at,dm_conversation_id,event_type,participant_ids"}
        res = await self._paginate(path, params, limit=limit, auth_type="oauth1")
        return self._convert_dm_events(res.data)

    async def create_group_conversation(self, participant_ids: list[str], text: str) -> MessageResponse:
        """Create a new group conversation with an initial message."""
        path = "dm_conversations"
        data = {
            "conversation_type": "Group",
            "participant_ids": participant_ids,
            "message": {"text": text},
        }
        res = await self._request("POST", path, json=data, auth_type="oauth1")
        dm_data = res.get("data", {})
        return MessageResponse(
            success=True,
            message_id=dm_data.get("dm_id") or dm_data.get("id"),
            platform="x",
            raw=res,
        )

    def _convert_dm_events(self, events: list[dict[str, Any]]) -> list[Message]:
        """Helper to convert DM event dictionaries to Message models."""
        messages = []
        for e in events:
            # Only process message create events for now (X supports Join/Leave too)
            event_type = e.get("event_type")
            if "text" not in e and event_type != "MessageCreate":
                continue

            messages.append(
                Message(
                    id=e["id"],
                    platform="x",
                    chat_id=e.get("dm_conversation_id"),
                    sender=UserInfo(id=e.get("sender_id"), platform="x"),
                    text=e.get("text"),
                    timestamp=datetime.fromisoformat(e["created_at"].replace("Z", "+00:00")),
                    raw=e,
                )
            )
        return messages

    # --- Direct Messages REST API v2 ---

    async def get_events_by_participant_id(
        self,
        participant_id: str,
        max_results: int | None = None,
        pagination_token: str | None = None,
        event_types: list[str] | None = None,
        dm_event_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        tweet_fields: list[str] | None = None,
    ) -> AsyncGenerator[GetEventsByParticipantIdResponse, None]:
        """
        Get DM events for a DM conversation
        Retrieves direct message events for a specific conversation.
        Runs automatically handling pagination.
        """
        pid = self._validate_path_param("participant_id", participant_id)
        path = f"dm_conversations/with/{pid}/dm_events"

        current_token = pagination_token
        while True:
            params: dict[str, Any] = {}
            if max_results is not None:
                params["max_results"] = max_results
            if event_types is not None:
                params["event_types"] = ",".join(str(item) for item in event_types)
            if dm_event_fields is not None:
                params["dm_event.fields"] = ",".join(str(item) for item in dm_event_fields)
            if expansions is not None:
                params["expansions"] = ",".join(str(item) for item in expansions)
            if media_fields is not None:
                params["media.fields"] = ",".join(str(item) for item in media_fields)
            if user_fields is not None:
                params["user.fields"] = ",".join(str(item) for item in user_fields)
            if tweet_fields is not None:
                params["tweet.fields"] = ",".join(str(item) for item in tweet_fields)
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", path, params=params, auth_type="oauth2_user_context")
            page_res = GetEventsByParticipantIdResponse.model_validate(res)
            yield page_res

            next_token = None
            if page_res.meta and page_res.meta.next_token:
                next_token = page_res.meta.next_token

            if not next_token:
                break
            current_token = next_token

    async def get_events_by_conversation_id(
        self,
        id: str,
        max_results: int | None = None,
        pagination_token: str | None = None,
        event_types: list[str] | None = None,
        dm_event_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        tweet_fields: list[str] | None = None,
    ) -> AsyncGenerator[GetEventsByConversationIdResponse, None]:
        """
        Get DM events for a DM conversation
        Retrieves direct message events for a specific conversation.
        """
        conv_id = self._validate_path_param("id", id)
        path = f"dm_conversations/{conv_id}/dm_events"

        current_token = pagination_token
        while True:
            params: dict[str, Any] = {}
            if max_results is not None:
                params["max_results"] = max_results
            if event_types is not None:
                params["event_types"] = ",".join(str(item) for item in event_types)
            if dm_event_fields is not None:
                params["dm_event.fields"] = ",".join(str(item) for item in dm_event_fields)
            if expansions is not None:
                params["expansions"] = ",".join(str(item) for item in expansions)
            if media_fields is not None:
                params["media.fields"] = ",".join(str(item) for item in media_fields)
            if user_fields is not None:
                params["user.fields"] = ",".join(str(item) for item in user_fields)
            if tweet_fields is not None:
                params["tweet.fields"] = ",".join(str(item) for item in tweet_fields)
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", path, params=params, auth_type="oauth2_user_context")
            page_res = GetEventsByConversationIdResponse.model_validate(res)
            yield page_res

            next_token = None
            if page_res.meta and page_res.meta.next_token:
                next_token = page_res.meta.next_token

            if not next_token:
                break
            current_token = next_token

    async def get_events_by_id(
        self,
        event_id: str,
        dm_event_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        tweet_fields: list[str] | None = None,
    ) -> GetEventsByIdResponse:
        """
        Get DM event by ID
        Retrieves details of a specific direct message event by its ID.
        """
        eid = self._validate_path_param("event_id", event_id)
        path = f"dm_events/{eid}"
        params: dict[str, Any] = {}
        if dm_event_fields is not None:
            params["dm_event.fields"] = ",".join(str(item) for item in dm_event_fields)
        if expansions is not None:
            params["expansions"] = ",".join(str(item) for item in expansions)
        if media_fields is not None:
            params["media.fields"] = ",".join(str(item) for item in media_fields)
        if user_fields is not None:
            params["user.fields"] = ",".join(str(item) for item in user_fields)
        if tweet_fields is not None:
            params["tweet.fields"] = ",".join(str(item) for item in tweet_fields)

        res = await self._request("GET", path, params=params, auth_type="oauth2_user_context")
        return GetEventsByIdResponse.model_validate(res)

    async def delete_events(self, event_id: str) -> DeleteEventsResponse:
        """
        Delete DM event
        Deletes a specific direct message event by its ID, if owned by the authenticated user.
        """
        eid = self._validate_path_param("event_id", event_id)
        path = f"dm_events/{eid}"
        res = await self._request("DELETE", path, auth_type="oauth2_user_context")
        return DeleteEventsResponse.model_validate(res)

    async def create_conversation(self, body: CreateConversationRequest) -> CreateConversationResponse:
        """
        Create DM conversation
        Initiates a new direct message conversation with specified participants.
        """
        path = "dm_conversations"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("POST", path, json=json_data, auth_type="oauth2_user_context")
        return CreateConversationResponse.model_validate(res)

    async def create_by_conversation_id(
        self, dm_conversation_id: str, body: CreateByConversationIdRequest
    ) -> CreateByConversationIdResponse:
        """
        Create DM message by conversation ID
        Sends a new direct message to a specific conversation by its ID.
        """
        conv = self._validate_path_param("dm_conversation_id", dm_conversation_id)
        path = f"dm_conversations/{conv}/messages"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("POST", path, json=json_data, auth_type="oauth2_user_context")
        return CreateByConversationIdResponse.model_validate(res)

    async def create_by_participant_id(
        self, participant_id: str, body: CreateByParticipantIdRequest
    ) -> CreateByParticipantIdResponse:
        """
        Create DM message by participant ID
        Sends a new direct message to a specific participant by their ID.
        """
        pid = self._validate_path_param("participant_id", participant_id)
        path = f"dm_conversations/with/{pid}/messages"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("POST", path, json=json_data, auth_type="oauth2_user_context")
        return CreateByParticipantIdResponse.model_validate(res)

    async def get_events(
        self,
        max_results: int | None = None,
        pagination_token: str | None = None,
        event_types: list[str] | None = None,
        dm_event_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        tweet_fields: list[str] | None = None,
    ) -> AsyncGenerator[GetEventsResponse, None]:
        """
        Get DM events
        Retrieves a list of recent direct message events across all conversations.
        """
        path = "dm_events"
        current_token = pagination_token
        while True:
            params: dict[str, Any] = {}
            if max_results is not None:
                params["max_results"] = max_results
            if event_types is not None:
                params["event_types"] = ",".join(str(item) for item in event_types)
            if dm_event_fields is not None:
                params["dm_event.fields"] = ",".join(str(item) for item in dm_event_fields)
            if expansions is not None:
                params["expansions"] = ",".join(str(item) for item in expansions)
            if media_fields is not None:
                params["media.fields"] = ",".join(str(item) for item in media_fields)
            if user_fields is not None:
                params["user.fields"] = ",".join(str(item) for item in user_fields)
            if tweet_fields is not None:
                params["tweet.fields"] = ",".join(str(item) for item in tweet_fields)
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", path, params=params, auth_type="oauth2_user_context")
            page_res = GetEventsResponse.model_validate(res)
            yield page_res

            next_token = None
            if page_res.meta and page_res.meta.next_token:
                next_token = page_res.meta.next_token

            if not next_token:
                break
            current_token = next_token
