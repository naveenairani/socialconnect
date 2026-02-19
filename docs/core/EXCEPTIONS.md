# Exceptions

`src/socialconnector/core/exceptions.py`

```
SocialConnectorError (base)
├── AuthenticationError        — invalid/expired credentials
├── RateLimitError             — rate limit hit, has retry_after: float
├── ProviderNotFoundError      — unknown provider name
├── MessageError               — send/edit/delete failed
├── WebhookError               — webhook setup failed
├── MediaError                 — media upload/download failed
└── ConfigurationError         — invalid config
```

All carry `platform: str`, `original_error: Exception | None`, and `details: dict`.
