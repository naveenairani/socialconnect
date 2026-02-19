# Twitter/X Provider

`src/socialconnector/providers/twitter.py`

- **Auth**: OAuth 2.0 Bearer token (app-only) or OAuth 1.0a (user context) → `OAuth2Auth`
- **SDK**: None (pure httpx)
- **API**: `https://api.twitter.com/2/`
- **Webhook**: Account Activity API (enterprise) or filtered stream
- **Polling**: Search/timeline endpoints
- **Features**: tweets, DMs, media, replies, likes
- **Rate limit**: Strict per-endpoint limits (varies by API tier: free/basic/pro)
- **Chat ID**: user ID for DMs, tweet ID for replies

## Key mappings

| Unified | Twitter API v2 |
|---------|---------------|
| `send_message` | `POST /2/dm_conversations/with/{id}/messages` (DM) or `POST /2/tweets` (tweet) |
| `send_media` | `POST /1.1/media/upload` then attach media_id |
| `delete_message` | `DELETE /2/tweets/{id}` |
| `get_messages` | `GET /2/dm_events` |
