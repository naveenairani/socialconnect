from typing import TYPE_CHECKING, Callable, Optional, Type

try:
    from importlib.metadata import entry_points
except ImportError:
    # For Python < 3.10
    from importlib_metadata import entry_points

from socialconnector.core.exceptions import ProviderNotFoundError

if TYPE_CHECKING:
    from socialconnector.core.base_adapter import BaseAdapter


class AdapterRegistry:
    """Singleton registry for provider adapters."""

    _instance: Optional["AdapterRegistry"] = None
    _adapters: dict[str, Type["BaseAdapter"]] = {}

    def __new__(cls) -> "AdapterRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, name: str, adapter_cls: Type["BaseAdapter"]) -> None:
        """Register a new adapter class."""
        self._adapters[name] = adapter_cls

    def get(self, name: str) -> Type["BaseAdapter"]:
        """Retrieve an adapter class by name."""
        if name not in self._adapters:
            raise ProviderNotFoundError(f"Provider '{name}' not found.")
        return self._adapters[name]

    def list(self) -> list[str]:
        """List all registered provider names."""
        return list(self._adapters.keys())

    def auto_discover(self) -> None:
        """Discover adapters via setuptools entry points."""
        eps = entry_points().select(group="socialconnector.providers")
        for entry in eps:
            adapter_cls = entry.load()
            self.register(entry.name, adapter_cls)


def register_adapter(name: str) -> Callable[[Type["BaseAdapter"]], Type["BaseAdapter"]]:
    """Class decorator for registering adapters."""

    def decorator(cls: Type["BaseAdapter"]) -> Type["BaseAdapter"]:
        AdapterRegistry().register(name, cls)
        return cls

    return decorator
