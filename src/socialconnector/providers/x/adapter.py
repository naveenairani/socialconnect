"""
X (formerly Twitter) adapter using API v2.
Modular implementation composing multiple domain-specific mixins.
"""

import time
from typing import Any

from socialconnector.core.auth import OAuth1Auth
from socialconnector.core.base_adapter import BaseAdapter
from socialconnector.core.exceptions import AuthenticationError, RateLimitError
from socialconnector.core.models import AdapterConfig, HealthStatus, WebhookConfig
from socialconnector.core.oauth2_pkce import OAuth2PKCEFlow, OAuth2Token

from ._account_activity import XAccountActivityMixin
from ._auth import BearerTokenManager
from ._chat import XChatMixin
from ._communities import XCommunitiesMixin
from ._compliance import XComplianceMixin
from ._connections import XConnectionsMixin
from ._dms import XDmsMixin
from ._general import XGeneralMixin
from ._http import XHttpMixin
from ._media import XMediaMixin
from ._news import XNewsMixin
from ._notes import XNotesMixin
from ._spaces import XSpacesMixin
from ._stream import XStreamMixin
from ._tweets import XTweetsMixin
from ._usage import XUsageMixin
from ._users import XUsersMixin


class XAdapter(
    XHttpMixin,
    XTweetsMixin,
    XUsersMixin,
    XDmsMixin,
    XComplianceMixin,
    XStreamMixin,
    XMediaMixin,
    XNewsMixin,
    XNotesMixin,
    XUsageMixin,
    XAccountActivityMixin,
    XChatMixin,
    XCommunitiesMixin,
    XConnectionsMixin,
    XGeneralMixin,
    XSpacesMixin,
    BaseAdapter,
):
    """X (formerly Twitter) adapter using API v2."""

    def __init__(
        self,
        config: AdapterConfig,
        http_client: Any,
        logger: Any,
    ) -> None:
        super().__init__(config, http_client, logger)

        self.access_token: str | None = None
        self.access_token_secret: str | None = None
        self._oauth2_user_access_token: str | None = None
        self._oauth2_pkce_flow: OAuth2PKCEFlow | None = None
        self.auth_strategy: str = "oauth2"
        self.auth: OAuth1Auth | None = None

        # Always initialize token manager (used for OAuth2 and some v2 endpoints)
        self.bearer_token_manager = BearerTokenManager(
            api_key=config.api_key or "",
            api_secret=config.api_secret or "",
            http_client=self.http_client,
            logger=self.logger,
            pre_supplied_token=None,
        )

        # Rate limit tracking
        self._rate_limit_remaining: int | None = None
        self._rate_limit_reset: float = 0
        self._last_request_time: float = 0

        # Attempt auto-setup from config or environment
        self.setup(
            api_key=config.api_key,
            api_secret=config.api_secret,
            access_token=config.extra.get("access_token"),
            access_token_secret=config.extra.get("access_token_secret"),
            bearer_token=config.extra.get("bearer_token"),
            oauth2_user_access_token=(
                config.extra.get("oauth2_user_access_token")
                or config.extra.get("user_access_token")
            )
        )
        self._init_oauth2_user_pkce(config)

    def setup(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        access_token: str | None = None,
        access_token_secret: str | None = None,
        bearer_token: str | None = None,
        oauth2_user_access_token: str | None = None,
    ) -> None:
        """
        Configure X adapter credentials. Falls back to environment variables.
        """
        import os

        # Use explicitly provided keys, or fallback to config, or fallback to ENV
        final_api_key = (
            api_key
            or self.config.api_key
            or os.getenv("X_API_KEY")
            or os.getenv("TWITTER_API_KEY")
        )
        final_api_secret = (
            api_secret
            or self.config.api_secret
            or os.getenv("X_API_SECRET")
            or os.getenv("TWITTER_API_SECRET")
        )
        final_access_tok = (
            access_token
            or os.getenv("X_ACCESS_TOKEN")
            or os.getenv("TWITTER_ACCESS_TOKEN")
        )
        final_access_sec = (
            access_token_secret
            or os.getenv("X_ACCESS_TOKEN_SECRET")
            or os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        )
        final_bearer = (
            bearer_token
            or os.getenv("X_BEARER_TOKEN")
            or os.getenv("TWITTER_BEARER_TOKEN")
        )

        self.access_token = final_access_tok
        self.access_token_secret = final_access_sec
        self._oauth2_user_access_token = oauth2_user_access_token

        # Update core config so it can be used generically
        if final_api_key:
            self.config.api_key = final_api_key
        if final_api_secret:
            self.config.api_secret = final_api_secret

        if final_api_key and final_api_secret and self.access_token and self.access_token_secret:
            self.auth_strategy = "oauth1"
            self.logger.debug("Using OAuth1 User-context auth for X")
            self.auth = OAuth1Auth(
                client_key=final_api_key,
                client_secret=final_api_secret,
                resource_owner_key=self.access_token,
                resource_owner_secret=self.access_token_secret,
            )
        else:
            self.auth_strategy = "oauth2"
            self.logger.debug("Using OAuth2 App-only auth for X")

        # Re-initialize token manager with new keys
        self.bearer_token_manager = BearerTokenManager(
            api_key=final_api_key or "",
            api_secret=final_api_secret or "",
            http_client=self.http_client,
            logger=self.logger,
            pre_supplied_token=final_bearer,
        )

        # Rate limit tracking
        self._rate_limit_remaining = None
        self._rate_limit_reset = 0
        self._last_request_time = 0

    async def _get_oauth2_user_token(self) -> str:
        """Return a configured OAuth2 user-context access token."""
        token = self._oauth2_user_access_token
        if token and isinstance(token, str) and token.strip():
            return token

        if self._oauth2_pkce_flow and self._oauth2_pkce_flow.token:
            flow_token = self._oauth2_pkce_flow.token
            if flow_token.access_token and not flow_token.is_expired:
                self._oauth2_user_access_token = flow_token.access_token
                return flow_token.access_token

            if flow_token.refresh_token:
                refreshed = await self._oauth2_pkce_flow.refresh(self.http_client)
                self._oauth2_user_access_token = refreshed.access_token
                return refreshed.access_token

        raise AuthenticationError(
            "OAuth2 user-context token is required for this endpoint",
            platform="x",
        )

    def _invalidate_oauth2_user_token(self) -> None:
        """Invalidate cached OAuth2 user-context token after a 401."""
        self._oauth2_user_access_token = None
        if self._oauth2_pkce_flow and self._oauth2_pkce_flow.token:
            self._oauth2_pkce_flow.token.access_token = ""
            self._oauth2_pkce_flow.token.expires_at = 0

    def _init_oauth2_user_pkce(self, config: AdapterConfig) -> None:
        """Initialize optional OAuth2 PKCE flow for user-context token management."""
        extra = config.extra
        client_id = extra.get("oauth2_client_id") or extra.get("client_id")
        redirect_uri = extra.get("oauth2_redirect_uri") or extra.get("redirect_uri")
        auth_url = extra.get("oauth2_authorization_url") or "https://x.com/i/oauth2/authorize"
        token_url = extra.get("oauth2_token_url") or "https://api.x.com/2/oauth2/token"
        client_secret = extra.get("oauth2_client_secret") or extra.get("client_secret")
        scopes = extra.get("oauth2_scopes") or extra.get("scopes")

        if isinstance(scopes, str):
            scopes_list = [s for s in scopes.split() if s]
        elif isinstance(scopes, list):
            scopes_list = [str(s) for s in scopes if str(s).strip()]
        else:
            scopes_list = []

        if client_id and redirect_uri:
            self._oauth2_pkce_flow = OAuth2PKCEFlow(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                token_url=token_url,
                authorization_url=auth_url,
                scopes=scopes_list,
            )

            token_dict = extra.get("oauth2_token")
            if isinstance(token_dict, dict) and token_dict.get("access_token"):
                expires_in = token_dict.get("expires_in")
                expires_at = token_dict.get("expires_at")
                if expires_at is None and isinstance(expires_in, int):
                    expires_at = time.time() + expires_in
                self._oauth2_pkce_flow.token = OAuth2Token(
                    access_token=token_dict["access_token"],
                    token_type=token_dict.get("token_type", "Bearer"),
                    expires_in=expires_in,
                    refresh_token=token_dict.get("refresh_token"),
                    scope=token_dict.get("scope"),
                    expires_at=expires_at,
                )
                if not self._oauth2_user_access_token and not self._oauth2_pkce_flow.token.is_expired:
                    self._oauth2_user_access_token = token_dict["access_token"]

    def get_oauth2_authorization_url(self, state: str | None = None) -> str:
        """Return OAuth2 PKCE authorization URL for user-context flows."""
        if not self._oauth2_pkce_flow:
            raise AuthenticationError(
                "OAuth2 PKCE is not configured (set oauth2_client_id and oauth2_redirect_uri).",
                platform="x",
            )
        return self._oauth2_pkce_flow.get_authorization_url(state)

    async def exchange_oauth2_code(self, code: str, code_verifier: str | None = None) -> dict[str, Any]:
        """Exchange OAuth2 authorization code for user token and cache it."""
        if not self._oauth2_pkce_flow:
            raise AuthenticationError(
                "OAuth2 PKCE is not configured (set oauth2_client_id and oauth2_redirect_uri).",
                platform="x",
            )
        token = await self._oauth2_pkce_flow.exchange_code(
            code=code, http_client=self.http_client, code_verifier=code_verifier
        )
        self._oauth2_user_access_token = token.access_token
        return token.to_dict()

    async def refresh_oauth2_user_token(self) -> dict[str, Any]:
        """Refresh OAuth2 user token using PKCE refresh token."""
        if not self._oauth2_pkce_flow:
            raise AuthenticationError(
                "OAuth2 PKCE is not configured (set oauth2_client_id and oauth2_redirect_uri).",
                platform="x",
            )
        token = await self._oauth2_pkce_flow.refresh(self.http_client)
        self._oauth2_user_access_token = token.access_token
        return token.to_dict()

    async def connect(self) -> None:
        """Validate credentials."""
        self.logger.info(f"Connecting to X (Auth: {self.auth_strategy})")

        if self.auth_strategy == "oauth1":
            # Verify we can reach users/me
            try:
                response_data = await self._request("GET", "users/me")
                if not response_data.get("data", {}).get("id"):
                    raise AuthenticationError("Invalid X credentials (no user data)", platform="x")
            except AuthenticationError:
                raise
            except RateLimitError as e:
                raise e
            except Exception as e:
                # Fix #3: Sanitize error logs to avoid information disclosure
                msg = "X authentication failed. Please check your credentials."
                raise AuthenticationError(msg, platform="x") from e
        else:
            # For App-only, just verify we can get a token
            await self.bearer_token_manager.get()
            return

    async def disconnect(self) -> None:
        """No provider-specific disconnect needed; client is shared."""
        pass

    async def health_check(self) -> HealthStatus:
        """Check if API is reachable."""
        try:
            await self.connect()
            return HealthStatus(provider="x", healthy=True)
        except Exception as e:
            self.logger.warning(f"X health check failed with {type(e).__name__}")
            return HealthStatus(provider="x", healthy=False, error="API unreachable or authentication failed")

    async def set_webhook(self, config: WebhookConfig) -> bool:
        """Enterprise/Premium only."""
        self.logger.warning("X webhooks require Enterprise/Premium tier (Account Activity API).")
        return False
