"""
X Direct Messages Mixin for managing conversations and messages.
"""

from datetime import datetime
from typing import Any

from socialconnector.core.models import Message, MessageResponse, UserInfo


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
