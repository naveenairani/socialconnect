# Auth

`src/socialconnector/core/auth.py`

Pluggable auth handling per provider.

## AuthProvider ABC

- `get_headers() -> dict` — returns auth headers for requests
- `refresh()` — async, refresh token if expired
- `is_valid() -> bool` — check if credentials are valid

## Implementations

| Class | For | Strategy |
|-------|-----|----------|
| `BearerTokenAuth` | Telegram, WhatsApp, Discord | Static bearer token in header |
| `OAuth2Auth` | Slack, Twitter | OAuth2 with token refresh |
| `ApiKeyAuth` | Aratai | API key + secret HMAC signing |

Each adapter picks the appropriate auth class in `connect()` based on `AdapterConfig`.
