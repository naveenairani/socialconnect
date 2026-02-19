# Slack Provider

`src/socialconnector/providers/slack.py`

- **Auth**: Bot token (xoxb-) or OAuth2 → `OAuth2Auth` or `BearerTokenAuth`
- **SDK**: `slack-sdk>=3.20`
- **API**: `https://slack.com/api/`
- **Webhook**: Slack Events API (requires URL verification challenge)
- **Polling**: Socket Mode (websocket-based, no public URL needed)
- **Features**: text (mrkdwn), media uploads, threads, reactions, blocks
- **Rate limit**: Tier-based (1-100+ req/min depending on method)
- **Chat ID**: channel ID (C...), DM ID (D...)

## Key mappings

| Unified | Slack API |
|---------|----------|
| `send_message` | `chat.postMessage` |
| `send_media` | `files.uploadV2` + `chat.postMessage` |
| `edit_message` | `chat.update` |
| `delete_message` | `chat.delete` |
| `get_messages` | `conversations.history` |
| `get_user_info` | `users.info` |
