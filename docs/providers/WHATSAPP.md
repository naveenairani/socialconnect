# WhatsApp Provider

`src/socialconnector/providers/whatsapp.py`

- **Auth**: Cloud API bearer token + phone_number_id → `BearerTokenAuth`
- **SDK**: None (pure httpx REST calls)
- **API**: `https://graph.facebook.com/v18.0/{phone_number_id}/messages`
- **Webhook**: Meta webhook verification (hub.verify_token challenge)
- **Polling**: Not supported (webhook only)
- **Features**: text, media (image/video/doc/audio), templates, interactive buttons/lists
- **Rate limit**: 80 msg/sec per phone number, 1000 unique users/24h (business tier)
- **Chat ID**: phone number in international format (e.g., "919876543210")

## Key mappings

| Unified | WhatsApp Cloud API |
|---------|--------------------|
| `send_message` | POST messages (type: text) |
| `send_media` | POST messages (type: image/document/video) |
| `edit_message` | Not supported → raise `MessageError` |
| `delete_message` | Not supported → raise `MessageError` |

## Extra config

`AdapterConfig.extra` needs: `phone_number_id`, `business_account_id`
