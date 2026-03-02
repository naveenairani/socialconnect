"""
Async OAuth2 PKCE (Proof Key for Code Exchange) flow.

Provider-agnostic — just configure the token and authorization URLs.
Uses httpx.AsyncClient so it integrates cleanly with the rest of the library.

Example::

    flow = OAuth2PKCEFlow(
        client_id="my_client",
        client_secret="my_secret",
        redirect_uri="https://example.com/callback",
        token_url="https://api.x.com/2/oauth2/token",
        authorization_url="https://x.com/i/oauth2/authorize",
        scopes=["dm.read", "tweet.read", "users.read", "offline.access"],
    )
    auth_url = flow.get_authorization_url()
    # ... user visits auth_url, pastes callback ...
    token = await flow.fetch_token(callback_url, http_client)
    print(token["access_token"])
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class OAuth2Token:
    """OAuth2 token bundle."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None
    expires_at: float | None = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > (self.expires_at - 10)

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


class OAuth2PKCEFlow:
    """
    OAuth2 PKCE authorization flow.

    Handles:
    - Code verifier / challenge generation (S256)
    - Authorization URL construction
    - Authorization code → token exchange
    - Token refresh

    Works with any OAuth2-PKCE compliant provider (X, GitHub, Google, etc.)
    """

    def __init__(
        self,
        client_id: str,
        redirect_uri: str,
        token_url: str,
        authorization_url: str,
        scopes: list[str],
        client_secret: str | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_url = token_url
        self.authorization_url = authorization_url
        self.scopes = scopes
        self._code_verifier: str | None = None
        self._code_challenge: str | None = None
        self.token: OAuth2Token | None = None

    # ------------------------------------------------------------------ #
    # PKCE helpers                                                         #
    # ------------------------------------------------------------------ #

    def _make_verifier(self) -> str:
        return secrets.token_urlsafe(96)[:128]

    def _make_challenge(self, verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def get_authorization_url(self, state: str | None = None) -> str:
        """Generate PKCE code verifier/challenge and return the auth URL.

        Call once per auth flow; the verifier is stored internally until
        ``fetch_token`` or ``exchange_code`` consumes it.
        """
        self._code_verifier = self._make_verifier()
        self._code_challenge = self._make_challenge(self._code_verifier)

        params: dict[str, str] = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "code_challenge": self._code_challenge,
            "code_challenge_method": "S256",
        }
        if state:
            params["state"] = state

        return f"{self.authorization_url}?{urllib.parse.urlencode(params)}"

    async def fetch_token(
        self,
        authorization_response: str,
        http_client: httpx.AsyncClient,
    ) -> OAuth2Token:
        """Exchange authorization code (from callback URL) for a token.

        Args:
            authorization_response: The full callback URL after the user authorizes.
            http_client: Shared ``httpx.AsyncClient`` from the adapter.

        Returns:
            ``OAuth2Token`` with access_token, refresh_token, etc.
        """
        parsed = urllib.parse.urlparse(authorization_response)
        qs = urllib.parse.parse_qs(parsed.query)
        if "code" not in qs:
            raise ValueError("No 'code' found in authorization_response URL")
        code = qs["code"][0]
        return await self.exchange_code(code, http_client)

    async def exchange_code(
        self,
        code: str,
        http_client: httpx.AsyncClient,
        code_verifier: str | None = None,
    ) -> OAuth2Token:
        """Exchange a raw authorization code for tokens.

        Args:
            code: The authorization code from the OAuth2 callback.
            http_client: Shared ``httpx.AsyncClient``.
            code_verifier: Override the stored verifier (optional).
        """
        verifier = code_verifier or self._code_verifier
        if not verifier:
            raise ValueError(
                "No code_verifier available. Call get_authorization_url() first."
            )

        data: dict[str, str] = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": verifier,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        auth: Any = None

        if self.client_secret:
            auth = (self.client_id, self.client_secret)
        else:
            # Public client: include client_id in body
            data["client_id"] = self.client_id

        response = await http_client.post(
            self.token_url, data=data, headers=headers, auth=auth
        )
        response.raise_for_status()
        return self._parse_token(response.json())

    async def refresh(self, http_client: httpx.AsyncClient) -> OAuth2Token:
        """Refresh the access token using the stored refresh token.

        Args:
            http_client: Shared ``httpx.AsyncClient``.
        """
        if not self.token or not self.token.refresh_token:
            raise ValueError("No refresh token available.")

        data: dict[str, str] = {
            "grant_type": "refresh_token",
            "refresh_token": self.token.refresh_token,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        auth: Any = None

        if self.client_secret:
            auth = (self.client_id, self.client_secret)
        else:
            data["client_id"] = self.client_id

        response = await http_client.post(
            self.token_url, data=data, headers=headers, auth=auth
        )
        response.raise_for_status()
        self.token = self._parse_token(response.json())
        return self.token

    # ------------------------------------------------------------------ #
    # Internals                                                            #
    # ------------------------------------------------------------------ #

    def _parse_token(self, raw: dict[str, Any]) -> OAuth2Token:
        expires_in = raw.get("expires_in")
        expires_at = time.time() + expires_in if expires_in else None
        self.token = OAuth2Token(
            access_token=raw["access_token"],
            token_type=raw.get("token_type", "Bearer"),
            expires_in=expires_in,
            refresh_token=raw.get("refresh_token"),
            scope=raw.get("scope"),
            expires_at=expires_at,
        )
        return self.token
