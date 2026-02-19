# Events

`src/socialconnector/core/events.py`

Lightweight async event bus for incoming platform events.

## EventBus class

- `subscribe(event_type: str, callback: Callable)` — register handler
- `unsubscribe(event_type: str, callback: Callable)` — remove handler
- `emit(event_type: str, event: Event)` — async, calls all handlers for that type
- Handlers are async callables: `async def handler(event: Event) -> None`

## Flow

```
Platform → Adapter normalizes to Event → adapter calls _emit() → EventBus → User callbacks
```

Supports wildcard `"*"` to catch all events.
