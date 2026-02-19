# Registry

`src/socialconnector/core/registry.py`

Singleton that maps provider name strings to adapter classes.

## API

- `register_adapter(name: str)` — class decorator, registers adapter class
- `get_adapter(name: str) -> type[BaseAdapter]` — returns adapter class or raises `ProviderNotFoundError`
- `list_adapters() -> list[str]` — returns registered provider names
- `auto_discover()` — scans setuptools entry point group `socialconnector.providers`

## Usage

```python
@register_adapter("telegram")
class TelegramAdapter(BaseAdapter):
    ...
```

Provider `__init__.py` imports all adapter modules to trigger registration.
