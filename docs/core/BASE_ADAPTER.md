# BaseAdapter

ABC that every provider must implement. Lives in `src/socialconnector/core/base_adapter.py`.

## Abstract Methods

| Method | Signature | Returns |
| --- | --- | --- |
| `connect` | `async def connect()` | `None` |
| `disconnect` | `async def disconnect()` | `None` |
| `health_check` | `async def health_check()` | `HealthStatus` |
| `send_message` | `async def send_message(chat_id, text, *, reply_to=None)` | `MessageResponse` |
| `send_media` | `async def send_media(chat_id, media, *, caption=None)` | `MessageResponse` |
| `edit_message` | `async def edit_message(chat_id, message_id, new_text)` | `MessageResponse` |
| `delete_message` | `async def delete_message(chat_id, message_id)` | `bool` |
| `get_messages` | `async def get_messages(chat_id, *, limit=50)` | `list[Message]` |
| `get_user_info` | `async def get_user_info(user_id)` | `UserInfo` |
| `set_webhook` | `async def set_webhook(config: WebhookConfig)` | `bool` |
| `start_polling` | `async def start_polling()` | `None` |
| `stop_polling` | `async def stop_polling()` | `None` |

## Concrete methods (inherited)

- `on(event_type, callback)` — register event handler
- `on_message(callback)` — decorator shortcut
- `_emit(event_type, data)` — fire event to handlers

## Rules

- Wrap platform errors in unified exceptions
- Return unified models only, never platform SDK objects
- Use shared infrastructure injected via the `AdapterFactory`

## Dependency Injection (DI)

To ensure adapters are testable and share internal resources (like connection pools), we inject dependencies through the constructor.

```python
class MyAdapter(BaseAdapter):
    def __init__(self, config, http_client, logger):
        super().__init__(config)
        self.client = http_client  # Injected
        self.logger = logger        # Injected
```

This allows us to pass a `MockHTTPClient` during unit tests, ensuring zero external network calls.
