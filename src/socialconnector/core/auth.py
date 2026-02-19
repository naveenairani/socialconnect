from abc import ABC, abstractmethod
from typing import Any


class AuthProvider(ABC):
    """Abstract base for authentication strategies."""

    @abstractmethod
    def get_headers(self) -> dict[str, str]:
        """Return authentication headers."""

    @abstractmethod
    async def refresh(self) -> None:
        """Refresh credentials if needed."""

    @abstractmethod
    def is_valid(self) -> bool:
        """Check if credentials are currently valid."""


class BearerTokenAuth(AuthProvider):
    """Simple bearer token authentication."""

    def __init__(self, token: str) -> None:
        self.token = token

    def get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    async def refresh(self) -> None:
        pass

    def is_valid(self) -> bool:
        return bool(self.token)


class OAuth2Auth(AuthProvider):
    """OAuth2 authentication with token refresh logic."""

    def __init__(
        self,
        token: str,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        self.token = token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret

    def get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    async def refresh(self) -> None:
        # Implementation for OAuth2 refresh would go here
        pass

    def is_valid(self) -> bool:
        return bool(self.token)


class ApiKeyAuth(AuthProvider):
    """Auth using API key and secret (can be used for HMAC)."""

    def __init__(self, api_key: str, api_secret: str | None = None) -> None:
        self.api_key = api_key
        self.api_secret = api_secret

    def get_headers(self) -> dict[str, str]:
        return {"X-API-Key": self.api_key}

    async def refresh(self) -> None:
        pass

    def is_valid(self) -> bool:
        return bool(self.api_key)


class OAuth1Auth(AuthProvider):
    """OAuth 1.0a authentication."""

    def __init__(
        self,
        client_key: str,
        client_secret: str,
        resource_owner_key: str | None = None,
        resource_owner_secret: str | None = None,
    ) -> None:
        self.client_key = client_key
        self.client_secret = client_secret
        self.resource_owner_key = resource_owner_key
        self.resource_owner_secret = resource_owner_secret

    @property
    def auth(self) -> Any:
        """Return the Authlib httpx-compatible auth object."""
        from authlib.integrations.httpx_client import OAuth1Auth as AuthlibOAuth1Auth

        return AuthlibOAuth1Auth(
            client_id=self.client_key,
            client_secret=self.client_secret,
            token=self.resource_owner_key,
            token_secret=self.resource_owner_secret,
        )

    def get_auth_token(self, method: str, url: str, body: Any = None) -> str:
        """Not used for httpx integration, but kept for compatibility."""
        return ""

    def get_headers(self) -> dict[str, str]:
        return {}

    async def refresh(self) -> None:
        pass

    def is_valid(self) -> bool:
        return bool(self.client_key and self.client_secret)


class OAuth2PKCEAuth(AuthProvider):
    """OAuth2 PKCE authentication, wrapping ``OAuth2PKCEFlow``."""

    def __init__(
        self,
        client_id: str,
        redirect_uri: str,
        token_url: str,
        authorization_url: str,
        scopes: list[str],
        client_secret: str | None = None,
    ) -> None:
        from socialconnector.core.oauth2_pkce import OAuth2PKCEFlow

        self.flow = OAuth2PKCEFlow(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            token_url=token_url,
            authorization_url=authorization_url,
            scopes=scopes,
        )

    def get_headers(self) -> dict[str, str]:
        if self.flow.token and self.flow.token.access_token:
            return {"Authorization": f"Bearer {self.flow.token.access_token}"}
        return {}

    async def refresh(self) -> None:

        # Callers should pass their shared http_client; this is a convenience shim.
        raise NotImplementedError(
            "Call flow.refresh(http_client) directly to refresh the token."
        )

    def is_valid(self) -> bool:
        if not self.flow.token:
            return False
        return not self.flow.token.is_expired
