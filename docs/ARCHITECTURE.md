# Architecture

## Core Patterns

### Factory Function Facade + Adapter + Registry

Standardizes provider interactions and object lifecycle while providing perfect IDE IntelliSense.

```text
User Code → SocialConnector (Factory Function) → AdapterFactory → AdapterRegistry → BaseAdapter → ConcreteAdapter (e.g., XAdapter)
```

- **BaseAdapter**: Abstract base for all providers.
- **AdapterRegistry**: Singleton for provider discovery.
- **AdapterFactory**: Decouples instantiation and dependency injection.

### Observer (Event Bus)

Platform events are normalized and broadcasted via `EventBus`. Supports wildcard `*` subscribers.

### Chain of Responsibility (Middleware)

Pipeline for pre/post-processing (Sanitization, Validation, Logging) using the "Onion" model.

## Resilience & Scalability

### Decorator Pattern

Cross-cutting concerns like logging or simple retries are wrapped around adapters to keep core logic clean.

### Circuit Breaker

Protects the system from failing APIs by "tripping" and failing fast when error thresholds are met.

### Dependency Injection (DI)

Adapters receive their HTTP clients, Loggers, and Configs via the Factory, making them fully unit-testable.

## Data Flow

```
Outgoing: User → Facade → [Middleware] → Adapter → Platform API
Incoming: Platform → Adapter → Normalize → Event Bus → [User Callbacks]
```

## Error Hierarchy (Unified)

`SocialConnectorError` → `AuthenticationError`, `RateLimitError`, `MessageError`, etc.

## Scalability

- **Zero-Touch Expansion**: New provider = 1 file in `providers/`.
- **Async-First**: Built on `asyncio` and `httpx`.
- **Resilient**: Built-in circuit breakers and rate limiting.
