import base64
import hashlib
import hmac as _hmac_mod
import secrets
import time
import urllib.parse
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

    def build_header(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        body: str | None = None,
    ) -> dict[str, str]:
        """Build an OAuth 1.0a Authorization header.

        Generates a pure Python HMAC-SHA1 signature per RFC 5849.

        Automatically includes query parameters (from `url` or `params`) and
        form-encoded `body` data in the signature. JSON or empty bodies are
        skipped as required by the OAuth1 specification.

        Args:
            method: HTTP verb (e.g., 'GET', 'POST').
            url: Full request URL (can include query string).
            params: Optional dict of query parameters.
            body: Optional raw request body string.

        Returns:
            A dict containing the 'Authorization' header.
        """
        import json as _json

        # ── 1. Split URL into base + existing query string ──
        parsed = urllib.parse.urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # Collect all non-OAuth query params that should go into the signature
        extra_params: dict[str, str] = {}
        if parsed.query:
            for k, vs in urllib.parse.parse_qs(parsed.query, keep_blank_values=True).items():
                extra_params[k] = vs[0]
        if params:
            for k, v in params.items():
                if v is not None:
                    extra_params[k] = str(v)

        # ── 2. Include body params only if form-encoded (not JSON) ──
        # Per RFC 5849 §3.4.1.3: only x-www-form-urlencoded bodies are signed.
        if body:
            is_json = False
            try:
                _json.loads(body)
                is_json = True
            except (ValueError, TypeError):
                pass

            if not is_json:
                for k, vs in urllib.parse.parse_qs(body, keep_blank_values=True).items():
                    extra_params[k] = vs[0]

        # ── 3. Build OAuth protocol parameters ──
        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(16)

        oauth_params: dict[str, str] = {
            "oauth_consumer_key": self.client_key,
            "oauth_nonce": nonce,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": timestamp,
            "oauth_version": "1.0",
        }
        if self.resource_owner_key:
            oauth_params["oauth_token"] = self.resource_owner_key

        # ── 4. Build signature base string ──
        all_params = {**extra_params, **oauth_params}
        sorted_pairs = sorted(
            (urllib.parse.quote(k, safe=""), urllib.parse.quote(str(v), safe=""))
            for k, v in all_params.items()
        )
        param_string = "&".join(f"{k}={v}" for k, v in sorted_pairs)

        encoded_base_url = urllib.parse.quote(base_url, safe="")
        encoded_params = urllib.parse.quote(param_string, safe="")
        signature_base = f"{method.upper()}&{encoded_base_url}&{encoded_params}"

        # ── 5. Sign with HMAC-SHA1 ──
        signing_key = (
            f"{urllib.parse.quote(self.client_secret, safe='')}"
            f"&{urllib.parse.quote(self.resource_owner_secret or '', safe='')}"
        )
        digest = _hmac_mod.new(
            signing_key.encode("utf-8"),
            signature_base.encode("utf-8"),
            hashlib.sha1,
        ).digest()
        signature = base64.b64encode(digest).decode("utf-8")
        oauth_params["oauth_signature"] = signature

        # ── 6. Build Authorization header string ──
        header_parts = ", ".join(
            f'{k}="{urllib.parse.quote(v, safe="")}"'
            for k, v in sorted(oauth_params.items())
        )
        return {"Authorization": f"OAuth {header_parts}"}


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
