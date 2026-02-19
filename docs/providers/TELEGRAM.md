# Telegram Provider

`src/socialconnector/providers/telegram.py`

- **Auth**: Bot token via BotFather → `BearerTokenAuth`
- **SDK**: `python-telegram-bot>=20.0`
- **API**: `https://api.telegram.org/bot{token}/`
- **Webhook**: Native support, `setWebhook` API
- **Polling**: `getUpdates` long-polling
- **Features**: text, media (photo/video/doc/sticker/voice), reply, edit, delete, inline keyboards
- **Rate limit**: 30 msg/sec globally, 1 msg/sec per chat
- **Chat ID**: numeric string, can be user or group

## Key mappings

| Unified | Telegram API |
|---------|-------------|
| `send_message` | `sendMessage` |
| `send_media` | `sendPhoto/sendDocument/sendVideo` |
| `edit_message` | `editMessageText` |
| `delete_message` | `deleteMessage` |
| `get_messages` | `getUpdates` (no history API) |
