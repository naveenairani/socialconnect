from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from socialconnector.core.models import (
    AdapterConfig,
    HealthStatus,
    Media,
    Message,
    MessageResponse,
    UserInfo,
    WebhookConfig,
)


class BaseAdapter(ABC):
    """Abstract base class for all social media provider adapters."""

    def __init__(
        self,
        config: AdapterConfig,
        http_client: Any,
        logger: Any,
    ) -> None:
        self.config = config
        self.http_client = http_client
        self.logger = logger
        self._handlers: dict[str, list[Callable]] = {}

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the platform."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close platform connections."""

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Check provider health."""

    @abstractmethod
    async def post(
        self,
        text: str,
        *,
        media: list[Media] | None = None,
    ) -> MessageResponse:
        """Create a public post or status update."""

    @abstractmethod
    async def direct_message(
        self,
        chat_id: str,
        text: str,
        *,
        reply_to: str | None = None,
    ) -> MessageResponse:
        """Send a private direct message."""

    @abstractmethod
    async def send_media(
        self,
        chat_id: str,
        media: Media,
        *,
        caption: str | None = None,
    ) -> MessageResponse:
        """Send a media attachment."""

    @abstractmethod
    async def edit_message(
        self,
        chat_id: str,
        message_id: str,
        new_text: str,
    ) -> MessageResponse:
        """Edit a message."""

    @abstractmethod
    async def delete_message(
        self,
        chat_id: str,
        message_id: str,
    ) -> bool:
        """Delete a message."""

    @abstractmethod
    async def get_messages(
        self,
        chat_id: str,
        *,
        limit: int = 50,
    ) -> list[Message]:
        """Fetch recent messages."""

    @abstractmethod
    async def get_user_info(self, user_id: str) -> UserInfo:
        """Get user information."""

    @abstractmethod
    async def set_webhook(self, config: WebhookConfig) -> bool:
        """Register a webhook."""

    @abstractmethod
    async def start_polling(self) -> None:
        """Start event polling."""

    @abstractmethod
    async def stop_polling(self) -> None:
        """Stop event polling."""

    def on(self, event_type: str, callback: Callable) -> None:
        """Register an event handler."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(callback)

    def on_message(self, callback: Callable) -> Callable:
        """Decorator shortcut for message events."""
        self.on("message_received", callback)
        return callback

    async def _emit(self, event_type: str, data: Any) -> None:
        """Fire an event to registered handlers."""
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            await handler(data)
