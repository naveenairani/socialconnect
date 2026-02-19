"""
X (Twitter) App-only Bearer Token Manager.

Handles fetching and caching the OAuth2 app-only bearer token from the
correct endpoint: https://api.twitter.com/oauth2/token
"""

import base64
from typing import Any


class BearerTokenManager:
    """Manages OAuth2 App-only bearer tokens for the X API.

    Fetches and caches the token so that only one round-trip is made
    per adapter lifetime. Supports manual invalidation on 401.
    """

    BEARER_TOKEN_URL = "https://api.twitter.com/oauth2/token"

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        http_client: Any,
        logger: Any,
        pre_supplied_token: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._http_client = http_client
        self._logger = logger
        self._token: str | None = pre_supplied_token

    @property
    def cached_token(self) -> str | None:
        return self._token

    def invalidate(self) -> None:
        """Clear cached token so the next call will re-fetch."""
        self._token = None

    async def get(self) -> str:
        """Return the cached bearer token, fetching a new one if needed."""
        if self._token:
            return self._token

        auth_str = f"{self._api_key}:{self._api_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()

        self._logger.debug("Fetching X App-only bearer token")
        response = await self._http_client.request(
            "POST",
            self.BEARER_TOKEN_URL,
            headers={"Authorization": f"Basic {encoded_auth}"},
            data={"grant_type": "client_credentials"},
        )
        response.raise_for_status()
        self._token = response.json().get("access_token")
        self._logger.debug("X bearer token fetched successfully")
        return self._token  # type: ignore[return-value]
