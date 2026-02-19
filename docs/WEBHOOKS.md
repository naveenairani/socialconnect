# Webhooks

`src/socialconnector/webhooks/`

## server.py

Lightweight ASGI server (using `uvicorn` + `starlette` or just raw ASGI) that exposes webhook endpoints.

- `WebhookServer(host, port)` — starts server
- Auto-routes: `POST /{provider}/webhook` → provider's webhook handler
- Handles platform-specific verification (Slack challenge, Meta hub.verify_token, Telegram secret_token)

## handlers.py

Per-provider verification and payload parsing:

- `verify_telegram(request)` — check secret_token header
- `verify_slack(request)` — respond to url_verification challenge, verify signing secret
- `verify_whatsapp(request)` — hub.verify_token GET challenge
- `parse_payload(provider, body)` → `Event`

Server is optional — users can integrate webhook handling into their own ASGI app instead.
