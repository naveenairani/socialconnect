# Testing

`tests/` mirrors `src/socialconnector/` structure.

## Strategy

- **Unit tests**: Mock HTTP calls with `httpx.MockTransport` or `respx`
- **conftest.py**: Shared fixtures — `fake_config`, `mock_client`, `sample_message`
- Each provider test: verify request format, response parsing, error mapping
- Core tests: registry, event bus, middleware pipeline, model validation

## Running

```bash
pytest                     # all tests
pytest tests/core/         # core only
pytest tests/providers/    # providers only
pytest --cov=socialconnector  # with coverage
```
