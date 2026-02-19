# Adapter Factory

The `AdapterFactory` is responsible for the lifecycle of provider adapters. It decouples the creation of specific adapters from the `SocialConnector` facade.

## Responsibilities

1. **Instantiation**: Retrieves the correct adapter class from the `AdapterRegistry`.
2. **Dependency Injection**: Injects required utilities like HTTP clients, loggers, and shared rate limiters.
3. **Configuration**: Validates and passes `AdapterConfig` to the instance.

## Pattern Flow

```python
# The Factory handles the "New-up" logic
adapter = AdapterFactory.create(
    provider="twitter",
    http_client=shared_client,
    logger=app_logger
)
```

## Benefits

- **Testability**: Allows injecting Mock HTTP clients for unit tests.
- **Single Responsibility**: `SocialConnector` only manages the facade; the Factory manages the objects.
- **Consistency**: Ensures all adapters are initialized with the same shared infrastructure.
