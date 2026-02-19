# Discord Provider

`src/socialconnector/providers/discord.py`

- **Auth**: Bot token → `BearerTokenAuth` (header: `Authorization: Bot {token}`)
- **SDK**: `discord.py>=2.3`
- **API**: `https://discord.com/api/v10/`
- **Webhook**: Discord Gateway (websocket)
- **Polling**: Gateway events (not HTTP polling)
- **Features**: text, embeds, media, reactions, threads, slash commands
- **Rate limit**: Global 50 req/sec, per-route limits in response headers
- **Chat ID**: channel snowflake ID

## Key mappings

| Unified | Discord API |
|---------|------------|
| `send_message` | `POST /channels/{id}/messages` |
| `send_media` | multipart POST with attachment |
| `edit_message` | `PATCH /channels/{id}/messages/{msg_id}` |
| `delete_message` | `DELETE /channels/{id}/messages/{msg_id}` |
| `get_messages` | `GET /channels/{id}/messages` |
