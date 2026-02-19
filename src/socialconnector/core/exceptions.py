from typing import Any, Optional


class SocialConnectorError(Exception):
    """Base exception for all SocialConnector errors."""

    def __init__(
        self,
        message: str,
        platform: str = "core",
        original_error: Optional[Exception] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.platform = platform
        self.original_error = original_error
        self.details = details or {}


class AuthenticationError(SocialConnectorError):
    """Raised when credentials are invalid or expired."""


class RateLimitError(SocialConnectorError):
    """Raised when platform rate limits are hit."""

    def __init__(
        self,
        message: str,
        platform: str,
        retry_after: float,
        original_error: Optional[Exception] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, platform, original_error, details)
        self.retry_after = retry_after


class ProviderNotFoundError(SocialConnectorError):
    """Raised when an unknown provider is requested."""


class MessageError(SocialConnectorError):
    """Raised when messaging operations fail."""


class WebhookError(SocialConnectorError):
    """Raised when webhook setup or validation fails."""


class MediaError(SocialConnectorError):
    """Raised when media operations fail."""


class ConfigurationError(SocialConnectorError):
    """Raised when invalid configuration is provided."""
