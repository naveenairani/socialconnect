"""
X Usage Mixin for retrieving API usage statistics from the X API v2.
"""

from socialconnector.core.models import UsageGetResponse


class XUsageMixin:
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
        p = {}
        if days is not None:
            p["days"] = days
        if usage_fields:
            p["usage.fields"] = ",".join(usage_fields)

        res = await self._request(
            "GET", "usage/tweets", params=p or None, auth_type="bearer_token"
        )
        return UsageGetResponse.model_validate(res)
