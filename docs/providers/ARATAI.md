# Aratai Provider

`src/socialconnector/providers/aratai.py`

- **Auth**: API key + secret → `ApiKeyAuth` (HMAC-signed requests)
- **SDK**: None (pure httpx REST calls)
- **API**: TBD — research Aratai's API docs and fill this in
- **Webhook**: TBD
- **Polling**: TBD
- **Features**: TBD (text messaging at minimum)

## Notes

Aratai API documentation needs to be researched before implementation. This adapter should follow the same pattern as WhatsApp (pure REST, no SDK dependency). Fill in the mappings table once API docs are available.
