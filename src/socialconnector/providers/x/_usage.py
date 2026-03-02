"""
X Usage Mixin for retrieving API usage statistics from the X API v2.
"""

from typing import TYPE_CHECKING, Any

from socialconnector.core.models import UsageGetResponse

if TYPE_CHECKING:
    import logging

    class XUsageMixinProtocol:
        logger: logging.Logger
        http_client: Any
        bearer_token_manager: Any
        auth_strategy: str
        auth: Any
        config: Any
        BASE_URL: str
        _request: Any
        _paginate: Any
        _emit: Any
        _validate_path_param: Any
        _get_oauth2_user_token: Any
        _invalidate_oauth2_user_token: Any
else:
    class XUsageMixinProtocol:
        pass



class XUsageMixin(XUsageMixinProtocol):
    """Mixin for X Usage API endpoints (/2/usage/*)."""

    async def get_usage_tweets(
        self,
        *,
        days: int | None = None,
        usage_fields: list[str] | None = None,
    ) -> UsageGetResponse:
        """
        Get usage statistics.
        Retrieves usage statistics for Posts over a specified number of days.

        Accepts BearerToken only (app-level credential required).
        """
        p: dict[str, Any] = {}
        if days is not None:
            p["days"] = days
        if usage_fields:
            p["usage.fields"] = ",".join(usage_fields)

        res = await self._request(
            "GET", "usage/tweets", params=p or None, auth_type="bearer_token"
        )
        return UsageGetResponse.model_validate(res)
