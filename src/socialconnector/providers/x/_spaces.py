"""
X Spaces Mixin for interacting with X Spaces endpoints.
"""

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from socialconnector.core.models import (
    SpaceGetBuyersResponse,
    SpaceGetByCreatorIdsResponse,
    SpaceGetByIdResponse,
    SpaceGetByIdsResponse,
    SpaceGetPostsResponse,
    SpaceSearchResponse,
)

if TYPE_CHECKING:
    import logging

    class XSpacesMixinProtocol:
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
    class XSpacesMixinProtocol:
        pass


class XSpacesMixin(XSpacesMixinProtocol):
    """Mixin for X Spaces API operations."""

    async def get_spaces_by_creator_ids(
        self,
        user_ids: list[str],
        *,
        space_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        user_fields: list[str] | None = None,
        topic_fields: list[str] | None = None,
    ) -> SpaceGetByCreatorIdsResponse:
        """
        Retrieves Spaces created by specified Users.
        Returns a structured SpaceGetByCreatorIdsResponse.
        """
        params: dict[str, Any] = {"user_ids": ",".join(user_ids)}
        if space_fields:
            params["space.fields"] = ",".join(space_fields)
        if expansions:
            params["expansions"] = ",".join(expansions)
        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if topic_fields:
            params["topic.fields"] = ",".join(topic_fields)

        res = await self._request("GET", "spacesByCreatorIds", params=params, auth_type="bearer_token")
        return SpaceGetByCreatorIdsResponse.model_validate(res)

    async def get_space_buyers(
        self,
        space_id: str,
        *,
        pagination_token: str | None = None,
        max_results: int | None = None,
        user_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        tweet_fields: list[str] | None = None,
    ) -> AsyncIterator[SpaceGetBuyersResponse]:
        """
        Retrieves a list of Users who purchased a ticket to a requested Space.
        Yields one page of results (SpaceGetBuyersResponse) at a time.
        """
        path = f"spaces/{self._validate_path_param('space_id', space_id)}/buyers"
        params: dict[str, Any] = {}
        if max_results:
            params["max_results"] = max_results
        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if expansions:
            params["expansions"] = ",".join(expansions)
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)

        current_token = pagination_token
        while True:
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", path, params=params, auth_type="bearer_token")
            page = SpaceGetBuyersResponse.model_validate(res)
            yield page

            current_token = page.meta.next_token if page.meta else None
            if not current_token:
                break

    async def search_spaces(
        self,
        query: str,
        *,
        state: str | None = None,
        max_results: int | None = None,
        space_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        user_fields: list[str] | None = None,
        topic_fields: list[str] | None = None,
    ) -> SpaceSearchResponse:
        """
        Searches for Spaces that match a specific query.
        Returns a structured SpaceSearchResponse.
        """
        params: dict[str, Any] = {"query": query}
        if state:
            params["state"] = state
        if max_results:
            params["max_results"] = max_results
        if space_fields:
            params["space.fields"] = ",".join(space_fields)
        if expansions:
            params["expansions"] = ",".join(expansions)
        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if topic_fields:
            params["topic.fields"] = ",".join(topic_fields)

        res = await self._request("GET", "spaces/search", params=params, auth_type="bearer_token")
        return SpaceSearchResponse.model_validate(res)

    async def get_space_by_id(
        self,
        space_id: str,
        *,
        space_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        user_fields: list[str] | None = None,
        topic_fields: list[str] | None = None,
    ) -> SpaceGetByIdResponse:
        """
        Retrieves details of a specific Space using its ID.
        Returns a structured SpaceGetByIdResponse.
        """
        path = f"spaces/{self._validate_path_param('space_id', space_id)}"
        params: dict[str, Any] = {}
        if space_fields:
            params["space.fields"] = ",".join(space_fields)
        if expansions:
            params["expansions"] = ",".join(expansions)
        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if topic_fields:
            params["topic.fields"] = ",".join(topic_fields)

        res = await self._request("GET", path, params=params, auth_type="bearer_token")
        return SpaceGetByIdResponse.model_validate(res)

    async def get_spaces_by_ids(
        self,
        ids: list[str],
        *,
        space_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        user_fields: list[str] | None = None,
        topic_fields: list[str] | None = None,
    ) -> SpaceGetByIdsResponse:
        """
        Retrieves details of multiple Spaces using their IDs.
        Returns a structured SpaceGetByIdsResponse.
        """
        params: dict[str, Any] = {"ids": ",".join(ids)}
        if space_fields:
            params["space.fields"] = ",".join(space_fields)
        if expansions:
            params["expansions"] = ",".join(expansions)
        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if topic_fields:
            params["topic.fields"] = ",".join(topic_fields)

        res = await self._request("GET", "spaces", params=params, auth_type="bearer_token")
        return SpaceGetByIdsResponse.model_validate(res)

    async def get_space_posts(
        self,
        space_id: str,
        *,
        pagination_token: str | None = None,
        max_results: int | None = None,
        tweet_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        poll_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        place_fields: list[str] | None = None,
    ) -> AsyncIterator[SpaceGetPostsResponse]:
        """
        Retrieves Posts shared in a specific Space.
        Yields one page of results (SpaceGetPostsResponse) at a time.
        """
        path = f"spaces/{self._validate_path_param('space_id', space_id)}/tweets"
        params: dict[str, Any] = {}
        if max_results:
            params["max_results"] = max_results
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)
        if expansions:
            params["expansions"] = ",".join(expansions)
        if media_fields:
            params["media.fields"] = ",".join(media_fields)
        if poll_fields:
            params["poll.fields"] = ",".join(poll_fields)
        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if place_fields:
            params["place.fields"] = ",".join(place_fields)

        current_token = pagination_token
        while True:
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", path, params=params, auth_type="bearer_token")
            page = SpaceGetPostsResponse.model_validate(res)
            yield page

            current_token = page.meta.next_token if page.meta else None
            if not current_token:
                break
