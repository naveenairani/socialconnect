from typing import Any

from socialconnector.core.models import AdapterConfig
from socialconnector.core.registry import AdapterRegistry
from socialconnector.utils.http_client import HTTPClient
from socialconnector.utils.logger import get_logger


class AdapterFactory:
    """Factory for creating and configuring provider adapters with DI."""

    @staticmethod
    def create(provider: str, http_client: HTTPClient, **config_kwargs: Any) -> Any:
        """Create a provider adapter instance with injected dependencies."""
        registry = AdapterRegistry()

        # Ensure provider is discovered/registered
        if provider not in registry.list():
            # Mapping for aliased modules
            module_map = {"twitter": "x"}
            module_name = module_map.get(provider, provider)

            try:
                import importlib

                importlib.import_module(f"socialconnector.providers.{module_name}")
            except ImportError:
                pass

        adapter_cls = registry.get(provider)

        # Separate known AdapterConfig fields from provider-specific extras.
        # This lets callers pass access_token, bearer_token, etc. directly
        # instead of wrapping them in an explicit extra={...} dict.
        known_fields = set(AdapterConfig.model_fields.keys())
        config_args: dict[str, Any] = {}
        extra: dict[str, Any] = dict(config_kwargs.pop("extra", {}))

        for key, value in config_kwargs.items():
            if key in known_fields:
                config_args[key] = value
            else:
                extra[key] = value

        # Create config with extras merged
        adapter_config = AdapterConfig(provider=provider, extra=extra, **config_args)

        # Initialize logger for this provider
        logger = get_logger(f"socialconnector.providers.{provider}")

        # Instantiate with DI
        return adapter_cls(config=adapter_config, http_client=http_client, logger=logger)
