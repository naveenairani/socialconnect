from typing import Any

from socialconnector.core.base_adapter import BaseAdapter
from socialconnector.core.exceptions import AuthenticationError, MessageError
from socialconnector.core.models import (
    AdapterConfig,
    HealthStatus,
    Media,
    Message,
    MessageResponse,
    UserInfo,
    WebhookConfig,
)
from socialconnector.core.registry import register_adapter


@register_adapter("telegram")
class TelegramAdapter(BaseAdapter):
    """Telegram Bot API adapter."""

    BASE_URL = "https://api.telegram.org/bot"

    def __init__(self, config: AdapterConfig, http_client: Any, logger: Any) -> None:
        super().__init__(config, http_client, logger)
        self.token = config.api_key
        self.api_url = f"{self.BASE_URL}{self.token}"

    async def connect(self) -> None:
        """Validate bot token."""
        url = f"{self.api_url}/getMe"
        self.logger.info("Connecting to Telegram...")
        response = await self.http_client.request("GET", url)

        if response.status_code == 401:
            self.logger.error("Invalid Telegram bot token")
            raise AuthenticationError("Invalid Telegram token", platform="telegram")
        response.raise_for_status()
        self.logger.info("Connected to Telegram successfully")

    async def disconnect(self) -> None:
        """No provider-specific disconnect needed."""
        pass

    async def health_check(self) -> HealthStatus:
        """Check bot health."""
        try:
            await self.connect()
            return HealthStatus(provider="telegram", healthy=True)
        except Exception as e:
            return HealthStatus(provider="telegram", healthy=False, error=str(e))

    async def post(
        self,
        text: str,
        *,
        media: list[Media] | None = None,
    ) -> MessageResponse:
        """Post a message (Telegram doesn't have public posts, mapping to sendMessage)."""
        return await self.direct_message(chat_id="none", text=text)

    async def direct_message(
        self,
        chat_id: str,
        text: str,
        *,
        reply_to: str | None = None,
    ) -> MessageResponse:
        """Send a telegram message."""
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_to:
            data["reply_to_message_id"] = reply_to

        self.logger.info(f"Sending Telegram message to {chat_id}")
        response = await self.http_client.request("POST", url, json=data)

        if response.status_code != 200:
            self.logger.error(f"Telegram message failed: {response.text}")
            raise MessageError(f"Telegram error: {response.text}", platform="telegram")

        res_data = response.json().get("result", {})
        return MessageResponse(
            success=True, message_id=str(res_data.get("message_id")), platform="telegram", raw=response.json()
        )

    async def send_media(
        self,
        chat_id: str,
        media: Media,
        *,
        caption: str | None = None,
    ) -> MessageResponse:
        """Not implemented in this basic example."""
        raise NotImplementedError("Media upload not supported on Telegram adapter yet.")

    async def edit_message(self, chat_id: str, message_id: str, new_text: str) -> MessageResponse:
        """Edit a telegram message."""
        url = f"{self.api_url}/editMessageText"
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": new_text,
        }
        response = await self.http_client.request("POST", url, json=data)
        response.raise_for_status()
        return MessageResponse(success=True, message_id=message_id, platform="telegram", raw=response.json())

    async def delete_message(self, chat_id: str, message_id: str) -> bool:
        """Delete a telegram message."""
        url = f"{self.api_url}/deleteMessage"
        data = {"chat_id": chat_id, "message_id": message_id}
        response = await self.http_client.request("POST", url, json=data)
        return response.status_code == 200

    async def get_messages(self, chat_id: str, *, limit: int = 50) -> list[Message]:
        return []

    async def get_user_info(self, user_id: str) -> UserInfo:
        return UserInfo(id=user_id, platform="telegram")

    async def set_webhook(self, config: WebhookConfig) -> bool:
        url = f"{self.api_url}/setWebhook"
        data = {"url": config.url}
        response = await self.http_client.request("POST", url, json=data)
        return response.status_code == 200

    async def start_polling(self) -> None:
        pass

    async def stop_polling(self) -> None:
        pass
