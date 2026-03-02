"""
X News Mixin for fetching AI-generated news stories from the X API v2.
"""



from typing import TYPE_CHECKING, Any

from socialconnector.core.models import (
    NewsGetResponse,
    NewsSearchResponse,
)

if TYPE_CHECKING:
    import logging

    class XNewsMixinProtocol:
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
    class XNewsMixinProtocol:
        pass



class XNewsMixin(XNewsMixinProtocol):
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
        p: dict[str, Any] = {"query": query}
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
