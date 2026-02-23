"""
X (formerly Twitter) adapter using API v2.
Modular implementation composing multiple domain-specific mixins.
"""

from typing import Any

from socialconnector.core.auth import OAuth1Auth
from socialconnector.core.base_adapter import BaseAdapter
from socialconnector.core.exceptions import AuthenticationError, RateLimitError
from socialconnector.core.models import AdapterConfig, HealthStatus, WebhookConfig

from ._account_activity import XAccountActivityMixin
from ._auth import BearerTokenManager
from ._chat import XChatMixin
from ._communities import XCommunitiesMixin
from ._compliance import XComplianceMixin
from ._dms import XDmsMixin
from ._http import XHttpMixin
from ._media import XMediaMixin
from ._notes import XNotesMixin
from ._stream import XStreamMixin
from ._tweets import XTweetsMixin
from ._users import XUsersMixin


class XAdapter(
    XHttpMixin,
    XTweetsMixin,
    XUsersMixin,
    XDmsMixin,
    XComplianceMixin,
    XStreamMixin,
    XMediaMixin,
    XNotesMixin,
    XAccountActivityMixin,
    XChatMixin,
    XCommunitiesMixin,
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

        # Determine auth strategy
        self.access_token = config.extra.get("access_token")
        self.access_token_secret = config.extra.get("access_token_secret")
        pre_supplied_bearer = config.extra.get("bearer_token")

        if self.access_token and self.access_token_secret:
            self.auth_strategy = "oauth1"
            self.auth = OAuth1Auth(
                client_key=config.api_key,
                client_secret=config.api_secret or "",
                resource_owner_key=self.access_token,
                resource_owner_secret=self.access_token_secret,
            )
        else:
            self.auth_strategy = "oauth2"
            self.logger.debug("Using OAuth2 App-only auth for X")

        # Always initialize token manager (used for OAuth2 and some v2 endpoints)
        self.bearer_token_manager = BearerTokenManager(
            api_key=config.api_key,
            api_secret=config.api_secret or "",
            http_client=self.http_client,
            logger=self.logger,
            pre_supplied_token=pre_supplied_bearer,
        )

        # Rate limit tracking
        self._rate_limit_remaining: int | None = None
        self._rate_limit_reset: float = 0
        self._last_request_time: float = 0

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
