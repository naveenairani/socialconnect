# Utils

`src/socialconnector/utils/`

## config.py
- `load_config(provider, *, env_prefix="SC_", dotenv_path=".env", **overrides) -> AdapterConfig`
- Auto-reads from env vars: `SC_TELEGRAM_API_KEY`, `SC_SLACK_API_KEY`, etc.

## http_client.py
- Shared `httpx.AsyncClient` with retry/backoff
- `get_client(base_url, timeout, max_retries) -> httpx.AsyncClient`
- Exponential backoff on 429/5xx

## rate_limiter.py
- Token bucket algorithm
- `RateLimiter(max_per_second: float)`
- `await limiter.acquire()` — blocks until a token is available

## logger.py
- `get_logger(name: str) -> logging.Logger`
- Structured JSON logging format
- Configurable via `SC_LOG_LEVEL` env var
