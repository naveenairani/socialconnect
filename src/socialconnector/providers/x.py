import base64
from typing import Any, Optional

from socialconnector.core.auth import OAuth1Auth
from socialconnector.core.base_adapter import BaseAdapter
from socialconnector.core.exceptions import (
    AuthenticationError,
    MessageError,
    RateLimitError,
)
from socialconnector.core.models import (
    AdapterConfig,
    HealthStatus,
    Media,
    Message,
    MessageResponse,
    UserInfo,
    WebhookConfig,
)
from socialconnector.core.registry import register_adapter


@register_adapter("x")
@register_adapter("twitter")
class XAdapter(BaseAdapter):
    """X (formerly Twitter) adapter using API v2."""

    BASE_URL = "https://api.x.com/2"

    def __init__(
        self,
        config: AdapterConfig,
        http_client: Any,
        logger: Any,
    ) -> None:
        super().__init__(config, http_client, logger)
        self._bearer_token: Optional[str] = None

        # Determine auth strategy
        self.access_token = config.extra.get("access_token")
        self.access_token_secret = config.extra.get("access_token_secret")
        self._bearer_token = config.extra.get("bearer_token")

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
            self.logger.debug("Using OAuth2 App-only auth for Twitter")

    async def _get_bearer_token(self) -> str:
        """Fetch an OAuth2 Bearer token (App-only auth)."""
        if self._bearer_token:
            return self._bearer_token

        auth_str = f"{self.config.api_key}:{self.config.api_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()

        self.logger.debug("Fetching new Twitter bearer token")
        response = await self.http_client.request(
            "POST",
            "https://api.x.com/2/oauth2/token",
            headers={
                "Authorization": f"Basic {encoded_auth}",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            },
            data="grant_type=client_credentials",
        )
        response.raise_for_status()
        self._bearer_token = response.json().get("access_token")
        return self._bearer_token

    async def _get_auth(self) -> Any:
        """Get the appropriate auth object or headers."""
        if self.auth_strategy == "oauth1":
            return self.auth.auth

        token = await self._get_bearer_token()
        return {"Authorization": f"Bearer {token}"}

    async def connect(self) -> None:
        """Validate credentials."""
        self.logger.info(f"Connecting to X (Auth: {self.auth_strategy})")
        if self.auth_strategy == "oauth1":
            url = f"{self.BASE_URL.strip()}/users/me"
            auth = await self._get_auth()
            response = await self.http_client.request("GET", url, auth=auth)
        else:
            # For App-only, just verify we can get a token
            await self._get_bearer_token()
            return

        if response.status_code == 401:
            self.logger.error(f"X authentication failed (401): {response.text}")
            raise AuthenticationError("Invalid X credentials", platform="x")
        
        if response.status_code == 429:
            self.logger.warning(
                f"X rate limit hit during connect. "
                f"Reset: {response.headers.get('x-rate-limit-reset')}, "
                f"Remaining: {response.headers.get('x-rate-limit-remaining')}, "
                f"Limit: {response.headers.get('x-rate-limit-limit')} "
                f"Body: {response.text}"
            )
            retry_after = float(response.headers.get("x-rate-limit-reset", 0))
            raise RateLimitError("X rate limit hit during connect", platform="x", retry_after=retry_after)

        response.raise_for_status()

    async def disconnect(self) -> None:
        """No provider-specific disconnect needed; client is shared."""
        pass

    async def health_check(self) -> HealthStatus:
        """Check if API is reachable."""
        try:
            await self.connect()
            return HealthStatus(provider="twitter", healthy=True)
        except Exception as e:
            self.logger.warning(f"X health check failed: {e}")
            return HealthStatus(provider="x", healthy=False, error=str(e))

    async def post(
        self,
        text: str,
        *,
        media: Optional[list[Media]] = None,
    ) -> MessageResponse:
        """Post a tweet."""
        if self.auth_strategy != "oauth1":
            self.logger.error("X posting requires OAuth 1.0a (User context)")
            raise AuthenticationError(
                "Posting tweets requires user access tokens (OAuth 1.0a)", 
                platform="x"
            )

        url = f"{self.BASE_URL.strip()}/tweets"
        data = {"text": text}
        # Multi-media support can be added here if implemented
        
        auth = await self._get_auth()

        self.logger.info(f"Posting tweet: {text[:30]}...")
        headers = {"Content-Type": "application/json"}
        if isinstance(auth, dict):
            headers.update(auth)
            response = await self.http_client.request(
                "POST", url, json=data, headers=headers
            )
        else:
            response = await self.http_client.request(
                "POST", url, json=data, auth=auth, headers=headers
            )

        if response.status_code == 429:
            reset_time = response.headers.get("x-rate-limit-reset")
            remaining = response.headers.get("x-rate-limit-remaining")
            limit = response.headers.get("x-rate-limit-limit")
            
            self.logger.warning(
                f"X rate limit hit during post. "
                f"Reset: {reset_time}, "
                f"Remaining: {remaining}, "
                f"Limit: {limit} "
                f"Body: {response.text}"
            )
            
            retry_after = float(reset_time or 0)
            raise RateLimitError(
                f"X rate limit hit. Body: {response.text}", 
                platform="x", 
                retry_after=retry_after
            )

        if response.status_code != 201:
            self.logger.error(f"Failed to post to X: {response.text}")
            raise MessageError(f"Failed to post to X: {response.text}", platform="x")

        res_data = response.json().get("data", {})
        self.logger.info(f"Post successful on X. ID: {res_data.get('id')}")

        return MessageResponse(
            success=True,
            message_id=res_data.get("id"),
            platform="x",
            raw=response.json(),
        )

    async def direct_message(
        self,
        chat_id: str,
        text: str,
        *,
        reply_to: Optional[str] = None,
    ) -> MessageResponse:
        """Send a true Twitter direct message (requires DM write permissions)."""
        # For now, providing a descriptive error as DM v2 is a separate scoped permission
        raise NotImplementedError(
            "Twitter direct_message (DMs) requires 'dm.write' scope and is not yet implemented. "
            "Use .post() for public status updates."
        )

    async def delete_message(self, chat_id: str, message_id: str) -> bool:
        """Delete a tweet."""
        url = f"{self.BASE_URL.strip()}/tweets/{message_id}"
        auth = await self._get_auth()

        self.logger.info(f"Deleting tweet: {message_id}")
        if isinstance(auth, dict):
            response = await self.http_client.request("DELETE", url, headers=auth)
        else:
            response = await self.http_client.request("DELETE", url, auth=auth)

        return response.status_code == 200

    async def send_media(
        self,
        chat_id: str,
        media: Media,
        *,
        caption: Optional[str] = None,
    ) -> MessageResponse:
        """Media upload is API v1.1. Not implemented in this basic v2 adapter."""
        raise NotImplementedError("Media upload not supported on Twitter v2 adapter yet.")

    async def edit_message(
        self, chat_id: str, message_id: str, new_text: str
    ) -> MessageResponse:
        """X does not support editing via API."""
        raise MessageError("X does not support editing", platform="x")

    async def get_messages(self, chat_id: str, *, limit: int = 50) -> list[Message]:
        """Free tier doesn't support easy history retrieval."""
        return []

    async def get_user_info(self, user_id: str) -> UserInfo:
        """Get user info."""
        url = f"{self.BASE_URL.strip()}/users/{user_id}"
        auth = await self._get_auth()

        if isinstance(auth, dict):
            response = await self.http_client.request("GET", url, headers=auth)
        else:
            response = await self.http_client.request("GET", url, auth=auth)

        response.raise_for_status()
        data = response.json().get("data", {})
        return UserInfo(
            id=data.get("id"),
            platform="x",
            username=data.get("username"),
            display_name=data.get("name"),
        )

    async def get_user_by_username(self, username: str) -> UserInfo:
        """Get user info by username handle."""
        url = f"{self.BASE_URL.strip()}/users/by/username/{username}"
        auth = await self._get_auth()

        if isinstance(auth, dict):
            response = await self.http_client.request("GET", url, headers=auth)
        else:
            response = await self.http_client.request("GET", url, auth=auth)

        response.raise_for_status()
        data = response.json().get("data", {})
        return UserInfo(
            id=data.get("id"),
            platform="x",
            username=data.get("username"),
            display_name=data.get("name"),
        )

    async def set_webhook(self, config: WebhookConfig) -> bool:
        """Enterprise/Premium only."""
        return False

    async def start_polling(self) -> None:
        """Not implemented."""
        pass

    async def stop_polling(self) -> None:
        """Not implemented."""
        pass
