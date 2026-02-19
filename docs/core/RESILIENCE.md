# Resilience Patterns

`src/socialconnector/core/resilience.py` (Proposed)

To ensure the SDK remains stable during platform outages or high traffic, we employ several resilience patterns.

## 1. Circuit Breaker

Prevents the application from repeatedly trying to call a failing API, which can lead to resource exhaustion and cascade failures.

### States

- **CLOSED**: Requests flow normally. Failures increment a counter.
- **OPEN**: Error threshold met. Requests fail instantly with `CircuitBreakerError`.
- **HALF-OPEN**: After a timeout, a single request is allowed to check if the service is back.

## 2. Decorators (Retry & Logging)

We use decorators to wrap `BaseAdapter` methods with additional logic without modifying the adapter's core code.

### Retry Decorator

Automatically retries failed requests based on an exponential backoff strategy or `Retry-After` headers.

```python
@retry(max_attempts=3, exceptions=(httpx.TimeoutException,))
async def send_message(self, ...):
    ...
```

## 3. Rate Limiting

Enforced at the provider level to prevent `429 Too Many Requests` errors.

- **Leaky Bucket**: Smooths out traffic spikes.
- **Fixed Window**: Ensures we don't exceed platform limits (e.g., 50 tweets per 24 hours).
