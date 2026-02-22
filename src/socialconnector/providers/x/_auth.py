import asyncio
import base64
import time
from typing import Any

from pydantic import SecretStr

from socialconnector.core.exceptions import AuthenticationError


class BearerTokenManager:
    """Manages OAuth2 App-only bearer tokens for the X API.

    Fetches and caches the token so that only one round-trip is made
    per adapter lifetime. Supports manual invalidation on 401.
    """

    BEARER_TOKEN_URL = "https://api.x.com/oauth2/token"

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        http_client: Any,
        logger: Any,
        pre_supplied_token: str | None = None,
    ) -> None:
        self._api_key = SecretStr(api_key)
        self._api_secret = SecretStr(api_secret)
        self._http_client = http_client
        self._logger = logger
        self._token: SecretStr | None = SecretStr(pre_supplied_token) if pre_supplied_token else None
        self._fetched_at = time.time() if pre_supplied_token else 0
        self._expires_in = 7200  # Default 2 hours
        self._lock = asyncio.Lock()

    def __repr__(self) -> str:
        """Secure representation that doesn't leak secrets."""
        token_status = '<present>' if self._token else '<absent>'
        return f"<{self.__class__.__name__} api_key=<masked> api_secret=<masked> token={token_status}>"

    @property
    def cached_token(self) -> str | None:
        return self._token.get_secret_value() if self._token else None

    def invalidate(self) -> None:
        """Clear cached token so the next call will re-fetch."""
        self._token = None

    async def get(self) -> str:
        """Return the cached bearer token, fetching a new one if needed (Fix #8: Refresh)."""
        if self._token:
            # Fast-path check for expiry without lock
            now = time.time()
            if now < (self._fetched_at + self._expires_in - 60):  # 60s buffer
                return self._token.get_secret_value()

        async with self._lock:
            # Check for expiry again inside lock
            if self._token:
                now = time.time()
                if now < (self._fetched_at + self._expires_in - 60):
                    return self._token.get_secret_value()
            self._logger.debug("X bearer token expired or empty, fetching new one")
            self.invalidate()

            auth_str = f"{self._api_key.get_secret_value()}:{self._api_secret.get_secret_value()}"
            encoded_auth = base64.b64encode(auth_str.encode()).decode()

            self._logger.debug("Fetching X App-only bearer token")
            try:
                response = await self._http_client.request(
                    "POST",
                    self.BEARER_TOKEN_URL,
                    headers={"Authorization": f"Basic {encoded_auth}"},
                    data={"grant_type": "client_credentials"},
                )
                response.raise_for_status()

                data = response.json()
                token = data.get("access_token")
                # X v2 token responses include expires_in (seconds)
                self._expires_in = data.get("expires_in", 7200)
                self._fetched_at = time.time()

                if not token or not isinstance(token, str) or not token.strip():
                    raise AuthenticationError("No valid access_token received from X", platform="x")

                self._token = SecretStr(token)
                self._logger.debug("X bearer token fetched successfully")
                return self._token.get_secret_value()

            except AuthenticationError:
                raise
            except Exception as e:
                self._logger.error(f"Failed to fetch X bearer token: {e}")
                raise AuthenticationError(f"Failed to fetch X bearer token: {e}", platform="x") from e
