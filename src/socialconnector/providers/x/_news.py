"""
X News Mixin for fetching AI-generated news stories from the X API v2.
"""

from socialconnector.core.models import (
    NewsGetResponse,
    NewsSearchResponse,
)


class XNewsMixin:
    """Mixin for X News API endpoints (/2/news/*)."""

    async def search_news(
        self,
        query: str,
        *,
        max_results: int | None = None,
        max_age_hours: int | None = None,
        news_fields: list[str] | None = None,
    ) -> NewsSearchResponse:
        """
        Search News.
        Retrieves a list of News stories matching the specified search query.

        Accepts BearerToken and OAuth2UserToken.
        """
        p: dict = {"query": query}
        if max_results is not None:
            p["max_results"] = max_results
        if max_age_hours is not None:
            p["max_age_hours"] = max_age_hours
        if news_fields:
            p["news.fields"] = ",".join(news_fields)

        res = await self._request("GET", "news/search", params=p)
        return NewsSearchResponse.model_validate(res)

    async def get_news_by_id(
        self,
        news_id: str,
        *,
        news_fields: list[str] | None = None,
    ) -> NewsGetResponse:
        """
        Get news story by ID.
        Retrieves a specific news story by its ID.

        Accepts BearerToken, OAuth2UserToken, and UserToken (OAuth1).
        """
        path = f"news/{self._validate_path_param('news_id', news_id)}"
        p = {}
        if news_fields:
            p["news.fields"] = ",".join(news_fields)

        res = await self._request("GET", path, params=p or None)
        return NewsGetResponse.model_validate(res)
