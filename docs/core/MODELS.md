# Models

Pydantic v2 models in `src/socialconnector/core/models.py`. All have `raw: dict = {}` for platform-specific data.

## Models List

| Model | Key Fields |
|-------|-----------|
| `AdapterConfig` | `provider, api_key, api_secret?, base_url?, timeout=30, max_retries=3, extra={}` |
| `Message` | `id, platform, chat_id, sender: UserInfo, text?, media: list[Media], timestamp, reply_to_id?` |
| `MessageResponse` | `success, message_id?, platform, timestamp` |
| `UserInfo` | `id, platform, username?, display_name?, avatar_url?, is_bot=False` |
| `Media` | `type: MediaType(image/video/audio/document/sticker), url?, file_bytes?, file_name?, mime_type?` |
| `WebhookConfig` | `url, secret?, events=["*"]` |
| `HealthStatus` | `provider, healthy, latency_ms?, error?, checked_at` |
| `Event` | `type: EventType, platform, chat_id?, user?, message?, timestamp` |

## EventType enum

`message_received`, `message_edited`, `message_deleted`, `reaction_added`, `user_joined`, `user_left`, `typing`, `custom`
