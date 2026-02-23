"""
X Communities API Mixin for retrieving and searching communities.
"""

from collections.abc import AsyncIterator
from typing import Any

from socialconnector.core.models import (
    GetByIdResponse,
    SearchResponse,
)


class XCommunitiesMixin:
    """Mixin for X Communities API operations (get_by_id, search)."""

    async def get_community_by_id(
        self, community_id: str, community_fields: list[str] | None = None
    ) -> GetByIdResponse:
        """
        Get Community by ID
        Retrieves details of a specific Community by its ID.
        """
        cid = self._validate_path_param("community_id", community_id)
        path = f"communities/{cid}"
        params: dict[str, Any] = {}
        if community_fields is not None:
            params["community.fields"] = ",".join(community_fields)

        res = await self._request("GET", path, params=params, auth_type="oauth2")
        return GetByIdResponse.model_validate(res)

    async def search_communities(
        self,
        query: str,
        max_results: int | None = None,
        pagination_token: str | None = None,
        community_fields: list[str] | None = None,
    ) -> AsyncIterator[SearchResponse]:
        """
        Search Communities
        Retrieves a list of Communities matching the specified search query.
        """
        path = "communities/search"

        current_token = pagination_token
        while True:
            params: dict[str, Any] = {"query": query}
            if max_results is not None:
                params["max_results"] = max_results
            if community_fields is not None:
                params["community.fields"] = ",".join(community_fields)
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", path, params=params, auth_type="oauth2")
            page_res = SearchResponse.model_validate(res)
            yield page_res

            next_token = None
            if page_res.meta and page_res.meta.next_token:
                next_token = page_res.meta.next_token

            if not next_token:
                break
            current_token = next_token
