from typing import Any, Callable, Coroutine

from socialconnector.core.models import Event


class EventBus:
    """Lightweight async event bus for unified platform events."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Event], Coroutine[Any, Any, None]]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Event], Coroutine[Any, Any, None]]) -> None:
        """Register a handler for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[Event], Coroutine[Any, Any, None]]) -> None:
        """Remove a handler for a specific event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    async def emit(self, event_type: str, event: Event) -> None:
        """Emit an event to all registered handlers for the type and wildcard."""
        # Call specific handlers
        handlers = self._subscribers.get(event_type, [])
        # Call wildcard handlers
        wildcard_handlers = self._subscribers.get("*", [])

        all_handlers = handlers + wildcard_handlers
        for handler in all_handlers:
            await handler(event)
