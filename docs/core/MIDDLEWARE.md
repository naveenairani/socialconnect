# Middleware

`src/socialconnector/core/middleware.py`

Optional pipeline for processing messages before/after they reach handlers.

## Interface

```python
async def my_middleware(context: dict, next: Callable) -> Any:
    # pre-processing
    result = await next(context)
    # post-processing
    return result
```

## Built-in Middleware

- `LoggingMiddleware` — logs all incoming/outgoing messages
- `RateLimitMiddleware` — enforces per-provider rate limits
- `ValidationMiddleware` — validates message content before sending

## Registration

```python
connector.use(LoggingMiddleware())
connector.use(RateLimitMiddleware(max_per_second=30))
```

Middleware executes in registration order (onion model).
