"""
X Tweets Mixin for managing posts, timelines, and searches.
"""

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TYPE_CHECKING, Any

from socialconnector.core.exceptions import MessageError
from socialconnector.core.models import (
    GetByIdsResponse,
    HideReplyRequest,
    HideReplyResponse,
    Media,
    MessageResponse,
    PaginatedResult,
    Tweet,
    TweetAnalyticsResponse,
    TweetCountsAllResponse,
    TweetCreateRequest,
    TweetCreateResponse,
    TweetDeleteResponse,
    TweetGetByIdResponse,
    TweetInsights28hrResponse,
    TweetInsightsHistoricalResponse,
    TweetLikingUsersResponse,
    TweetQuotedResponse,
    TweetRepostsResponse,
    TweetRetweetedByResponse,
    TweetSearchAllResponse,
    TweetSearchRecentResponse,
)

if TYPE_CHECKING:
    import logging

    class XTweetsMixinProtocol:
        logger: logging.Logger
        http_client: Any
        bearer_token_manager: Any
        auth_strategy: str
        auth: Any
        config: Any
        BASE_URL: str
        _request: Callable[..., Awaitable[Any]]
        _paginate: Callable[..., Awaitable[PaginatedResult]]
        _validate_path_param: Callable[[str, Any], str]
        _get_oauth2_user_token: Callable[[], Awaitable[Any]]
        _invalidate_oauth2_user_token: Callable[[], None]
        async def _upload_media(self, media: Media) -> str: ...
else:
    class XTweetsMixinProtocol:
        pass

class XTweetsMixin(XTweetsMixinProtocol):
    """Mixin for tweet-related operations (post, delete, lookup, search)."""

    async def post(
        self,
        text: str,
        *,
        media: list[Media] | None = None,
        reply_to_id: str | None = None,
        quote_tweet_id: str | None = None,
    ) -> MessageResponse:
        """Post a tweet with optional media, reply, or quote."""
        data: dict[str, Any] = {"text": text}

        if reply_to_id:
            data["reply"] = {"in_reply_to_tweet_id": reply_to_id}
        if quote_tweet_id:
            data["quote_tweet_id"] = quote_tweet_id

        if media:
            media_ids = []
            for m in media:
                mid = await self._upload_media(m)
                media_ids.append(mid)
            data["media"] = {"media_ids": media_ids}

        self.logger.info(f"Posting tweet: {text[:30]}...")
        res = await self._request("POST", "tweets", json=data, auth_type="oauth1")

        tweet_data = res.get("data", {})
        return MessageResponse(
            success=True,
            message_id=tweet_data.get("id"),
            platform="x",
            raw=res,
        )

    async def create_tweet(self, request: TweetCreateRequest) -> TweetCreateResponse:
        """
        Create a new Post or edit an existing one (via Edit Tweets).
        Full-featured creation supporting polls, geo, media tagging, etc.
        """
        payload = request.model_dump(exclude_none=True)
        res = await self._request("POST", "tweets", json=payload, auth_type="oauth1")
        return TweetCreateResponse.model_validate(res)

    async def delete_message(self, chat_id: str, message_id: str) -> bool:
        """Delete a tweet."""
        self.logger.info(f"Deleting tweet: {message_id}")
        try:
            path = f"tweets/{self._validate_path_param('message_id', message_id)}"
            await self._request("DELETE", path, auth_type="oauth1")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete tweet {message_id}: {e}")
            return False

    async def delete_tweet(self, tweet_id: str) -> TweetDeleteResponse:
        """
        Delete a specific Post by its ID.
        Returns a structured TweetDeleteResponse.
        """
        path = f"tweets/{self._validate_path_param('tweet_id', tweet_id)}"
        res = await self._request("DELETE", path, auth_type="oauth1")
        return TweetDeleteResponse.model_validate(res)

    async def hide_reply(self, tweet_id: str, request: HideReplyRequest) -> HideReplyResponse:
        """
        Hides or unhides a reply to a conversation owned by the authenticated user.
        """
        path = f"tweets/{self._validate_path_param('tweet_id', tweet_id)}/hidden"
        payload = request.model_dump(exclude_none=True)
        res = await self._request("PUT", path, json=payload, auth_type="oauth2")
        return HideReplyResponse.model_validate(res)

    async def get_tweet(self, tweet_id: str) -> Tweet:
        """Get a single tweet by ID."""
        params = {
            "tweet.fields": "author_id,created_at,conversation_id,in_reply_to_user_id,referenced_tweets,public_metrics"
        }
        res = await self._request("GET", f"tweets/{self._validate_path_param('tweet_id', tweet_id)}", params=params)
        data = res.get("data", {})
        return Tweet(**data, raw=res)

    async def get_tweet_analytics(
        self,
        tweet_ids: list[str],
        start_time: str,
        end_time: str,
        granularity: str,
        analytics_fields: list[str] | None = None,
    ) -> TweetAnalyticsResponse:
        """
        Retrieves analytics data for specified Posts within a defined time range.
        Up to 100 IDs are allowed.
        """
        params = {
            "ids": ",".join(tweet_ids),
            "start_time": start_time,
            "end_time": end_time,
            "granularity": granularity,
        }
        if analytics_fields:
            params["analytics.fields"] = ",".join(analytics_fields)

        res = await self._request("GET", "tweets/analytics", params=params, auth_type="oauth2")
        return TweetAnalyticsResponse.model_validate(res)

    async def get_insights_28hr(
        self,
        tweet_ids: list[str],
        granularity: str,
        requested_metrics: list[str],
        engagement_fields: list[str] | None = None,
    ) -> TweetInsights28hrResponse:
        """
        Retrieves engagement metrics for specified Posts over the last 28 hours.
        """
        params = {
            "tweet_ids": ",".join(tweet_ids),
            "granularity": granularity,
            "requested_metrics": ",".join(requested_metrics),
        }
        if engagement_fields:
            params["engagement.fields"] = ",".join(engagement_fields)

        res = await self._request("GET", "insights/28hr", params=params, auth_type="oauth2")
        return TweetInsights28hrResponse.model_validate(res)

    async def get_insights_historical(
        self,
        tweet_ids: list[str],
        start_time: str,
        end_time: str,
        granularity: str,
        requested_metrics: list[str],
        engagement_fields: list[str] | None = None,
    ) -> TweetInsightsHistoricalResponse:
        """
        Retrieves historical engagement metrics for specified Posts within a defined time range.
        """
        params = {
            "tweet_ids": ",".join(tweet_ids),
            "start_time": start_time,
            "end_time": end_time,
            "granularity": granularity,
            "requested_metrics": ",".join(requested_metrics),
        }
        if engagement_fields:
            params["engagement.fields"] = ",".join(engagement_fields)

        res = await self._request("GET", "insights/historical", params=params, auth_type="oauth2")
        return TweetInsightsHistoricalResponse.model_validate(res)

    async def get_tweet_by_id(
        self,
        tweet_id: str,
        *,
        tweet_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        poll_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        place_fields: list[str] | None = None,
    ) -> TweetGetByIdResponse:
        """
        Retrieves details of a specific Post by its ID.
        Supports full field selection and expansions.
        """
        path = f"tweets/{self._validate_path_param('tweet_id', tweet_id)}"
        params: dict[str, Any] = {}
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

        res = await self._request("GET", path, params=params)
        return TweetGetByIdResponse.model_validate(res)

    async def get_tweets(self, ids: list[str]) -> list[Tweet]:
        """Get multiple tweets by IDs."""
        params = {
            "ids": ",".join(ids),
            "tweet.fields": "author_id,created_at,conversation_id,in_reply_to_user_id,referenced_tweets,public_metrics",
        }
        res = await self._request("GET", "tweets", params=params)
        data = res.get("data", [])
        return [Tweet(**tweet, raw=res) for tweet in data]

    async def get_tweets_by_ids(
        self,
        ids: list[str],
        *,
        tweet_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        poll_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        place_fields: list[str] | None = None,
    ) -> GetByIdsResponse:
        """
        Get details of multiple Posts by their IDs.
        Retrieves details of multiple Posts by their IDs.
        """
        params: dict[str, Any] = {"ids": ",".join(ids)}
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

        res = await self._request("GET", "tweets", params=params)
        return GetByIdsResponse.model_validate(res)

    async def send_media(
        self,
        chat_id: str,
        media: Media,
        *,
        caption: str | None = None,
    ) -> MessageResponse:
        """Send a media attachment (tweet with media)."""
        return await self.post(text=caption or "", media=[media])

    async def edit_message(self, chat_id: str, message_id: str, new_text: str) -> MessageResponse:
        """X does not support editing via API."""
        raise MessageError("X does not support editing", platform="x")

    async def get_home_timeline(self, user_id: str, *, limit: int = 50) -> PaginatedResult:
        """Get the reverse-chronological timeline for the authenticated user."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/timelines/reverse_chronological"
        params = {
            "tweet.fields": "author_id,created_at,conversation_id,in_reply_to_user_id,referenced_tweets,public_metrics"
        }
        return await self._paginate(path, params, limit=limit, auth_type="oauth1")

    async def get_user_tweets(self, user_id: str, *, limit: int = 50) -> PaginatedResult:
        """Get tweets from a specific user."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/tweets"
        params = {
            "tweet.fields": "author_id,created_at,conversation_id,in_reply_to_user_id,referenced_tweets,public_metrics"
        }
        return await self._paginate(path, params, limit=limit)

    async def get_user_mentions(self, user_id: str, *, limit: int = 50) -> PaginatedResult:
        """Get mentions for a specific user."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/mentions"
        params = {
            "tweet.fields": "author_id,created_at,conversation_id,in_reply_to_user_id,referenced_tweets,public_metrics"
        }
        return await self._paginate(path, params, limit=limit)

    async def get_list_tweets(
        self, list_id: str, *, limit: int = 100,
        tweet_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        poll_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        place_fields: list[str] | None = None,
    ) -> PaginatedResult:
        """Get tweets from a list."""
        path = f"lists/{self._validate_path_param('list_id', list_id)}/tweets"
        fields = [
            ("tweet.fields", tweet_fields),
            ("expansions", expansions),
            ("media.fields", media_fields),
            ("poll.fields", poll_fields),
            ("user.fields", user_fields),
            ("place.fields", place_fields),
        ]
        p = {k: ",".join(v) for k, v in fields if v}
        return await self._paginate(path, params=p or None, limit=limit)

    async def search_tweets(self, query: str, *, limit: int = 50, all_history: bool = False) -> PaginatedResult:
        """Search for tweets. all_history=True requires Academic/Pro tier."""
        path = "tweets/search/all" if all_history else "tweets/search/recent"
        params = {
            "query": query,
            "tweet.fields": "author_id,created_at,conversation_id,in_reply_to_user_id,referenced_tweets,public_metrics",
        }
        # X recent search requires max_results >= 10; fetch at least 10 and trim locally.
        requested_limit = max(1, limit)
        page_limit = max(requested_limit, 10)
        res = await self._paginate(path, params, limit=page_limit)
        if requested_limit < page_limit:
            res.data = res.data[:requested_limit]
            res.result_count = len(res.data)
        return res

    async def search_tweets_full_archive(
        self,
        query: str,
        *,
        start_time: str | None = None,
        end_time: str | None = None,
        since_id: str | None = None,
        until_id: str | None = None,
        max_results: int | None = None,
        sort_order: str | None = None,
        exclude: list[str] | None = None,
        tweet_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        poll_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        place_fields: list[str] | None = None,
        pagination_token: str | None = None,
        next_token: str | None = None,
    ) -> AsyncIterator[TweetSearchAllResponse]:
        """
        Search all Posts from the full archive.
        Yields one page of results (TweetSearchAllResponse) at a time.
        """
        params: dict[str, Any] = {"query": query}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if since_id:
            params["since_id"] = since_id
        if until_id:
            params["until_id"] = until_id
        if max_results:
            params["max_results"] = max_results
        if sort_order:
            params["sort_order"] = sort_order
        if exclude:
            params["exclude"] = ",".join(exclude)
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

        current_token = pagination_token or next_token
        while True:
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", "tweets/search/all", params=params, auth_type="bearer_token")
            page = TweetSearchAllResponse.model_validate(res)
            yield page

            current_token = page.meta.next_token if page.meta else None
            if not current_token:
                break

    async def search_tweets_recent(
        self,
        query: str,
        *,
        start_time: str | None = None,
        end_time: str | None = None,
        since_id: str | None = None,
        until_id: str | None = None,
        max_results: int | None = None,
        sort_order: str | None = None,
        exclude: list[str] | None = None,
        tweet_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        poll_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        place_fields: list[str] | None = None,
        pagination_token: str | None = None,
        next_token: str | None = None,
    ) -> AsyncIterator[TweetSearchRecentResponse]:
        """
        Search for Posts from the last 7 days.
        Yields one page of results (TweetSearchRecentResponse) at a time.
        """
        params: dict[str, Any] = {"query": query}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if since_id:
            params["since_id"] = since_id
        if until_id:
            params["until_id"] = until_id
        if max_results:
            params["max_results"] = max_results
        if sort_order:
            params["sort_order"] = sort_order
        if exclude:
            params["exclude"] = ",".join(exclude)
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

        current_token = pagination_token or next_token
        while True:
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", "tweets/search/recent", params=params, auth_type="bearer_token")
            page = TweetSearchRecentResponse.model_validate(res)
            yield page

            current_token = page.meta.next_token if page.meta else None
            if not current_token:
                break

    async def get_retweeted_by(
        self,
        tweet_id: str,
        *,
        max_results: int | None = None,
        pagination_token: str | None = None,
        next_token: str | None = None,
        user_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        tweet_fields: list[str] | None = None,
    ) -> AsyncIterator[TweetRetweetedByResponse]:
        """
        Retrieves a list of Users who retweeted a specific Post by its ID.
        Yields one page of results (TweetRetweetedByResponse) at a time.
        """
        path = f"tweets/{self._validate_path_param('tweet_id', tweet_id)}/retweeted_by"
        params: dict[str, Any] = {}
        if max_results:
            params["max_results"] = max_results
        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if expansions:
            params["expansions"] = ",".join(expansions)
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)

        current_token = pagination_token or next_token
        while True:
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", path, params=params)
            page = TweetRetweetedByResponse.model_validate(res)
            yield page

            current_token = page.meta.next_token if page.meta else None
            if not current_token:
                break

    async def get_reposts(
        self,
        tweet_id: str,
        *,
        max_results: int | None = None,
        pagination_token: str | None = None,
        next_token: str | None = None,
        tweet_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        poll_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        place_fields: list[str] | None = None,
    ) -> AsyncIterator[TweetRepostsResponse]:
        """
        Retrieves a list of Posts that repost a specific Post by its ID.
        Yields one page of results (TweetRepostsResponse) at a time.
        """
        path = f"tweets/{self._validate_path_param('tweet_id', tweet_id)}/retweets"
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

        current_token = pagination_token or next_token
        while True:
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", path, params=params)
            page = TweetRepostsResponse.model_validate(res)
            yield page

            current_token = page.meta.next_token if page.meta else None
            if not current_token:
                break

    async def get_quoted_tweets(
        self,
        tweet_id: str,
        *,
        max_results: int | None = None,
        pagination_token: str | None = None,
        next_token: str | None = None,
        exclude: list[str] | None = None,
        tweet_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        poll_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        place_fields: list[str] | None = None,
    ) -> AsyncIterator[TweetQuotedResponse]:
        """
        Retrieves a list of Posts that quote a specific Post by its ID.
        Yields one page of results (TweetQuotedResponse) at a time.
        """
        path = f"tweets/{self._validate_path_param('tweet_id', tweet_id)}/quote_tweets"
        params: dict[str, Any] = {}
        if max_results:
            params["max_results"] = max_results
        if exclude:
            params["exclude"] = ",".join(exclude)
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

        current_token = pagination_token or next_token
        while True:
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", path, params=params)
            page = TweetQuotedResponse.model_validate(res)
            yield page

            current_token = page.meta.next_token if page.meta else None
            if not current_token:
                break

    async def get_liking_users(
        self,
        tweet_id: str,
        *,
        max_results: int | None = None,
        pagination_token: str | None = None,
        next_token: str | None = None,
        user_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        tweet_fields: list[str] | None = None,
    ) -> AsyncIterator[TweetLikingUsersResponse]:
        """
        Retrieves a list of Users who liked a specific Post by its ID.
        Yields one page of results (TweetLikingUsersResponse) at a time.
        """
        path = f"tweets/{self._validate_path_param('tweet_id', tweet_id)}/liking_users"
        params: dict[str, Any] = {}
        if max_results:
            params["max_results"] = max_results
        if user_fields:
            params["user.fields"] = ",".join(user_fields)
        if expansions:
            params["expansions"] = ",".join(expansions)
        if tweet_fields:
            params["tweet.fields"] = ",".join(tweet_fields)

        current_token = pagination_token or next_token
        while True:
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", path, params=params)
            page = TweetLikingUsersResponse.model_validate(res)
            yield page

            current_token = page.meta.next_token if page.meta else None
            if not current_token:
                break

    async def get_tweet_counts_all(
        self,
        query: str,
        *,
        start_time: str | None = None,
        end_time: str | None = None,
        since_id: str | None = None,
        until_id: str | None = None,
        granularity: str | None = None,
        search_count_fields: list[str] | None = None,
        pagination_token: str | None = None,
        next_token: str | None = None,
    ) -> AsyncIterator[TweetCountsAllResponse]:
        """
        Retrieves the count of Posts matching a search query from the full archive.
        Yields one page of results (TweetCountsAllResponse) at a time.
        """
        params: dict[str, Any] = {"query": query}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if since_id:
            params["since_id"] = since_id
        if until_id:
            params["until_id"] = until_id
        if granularity:
            params["granularity"] = granularity
        if search_count_fields:
            params["search_count.fields"] = ",".join(search_count_fields)

        current_token = pagination_token or next_token
        while True:
            if current_token:
                params["pagination_token"] = current_token

            res = await self._request("GET", "tweets/counts/all", params=params, auth_type="bearer_token")
            page = TweetCountsAllResponse.model_validate(res)
            yield page

            current_token = page.meta.next_token if page.meta else None
            if not current_token:
                break

    async def get_tweet_counts_recent(
        self,
        query: str,
        *,
        start_time: str | None = None,
        end_time: str | None = None,
        since_id: str | None = None,
        until_id: str | None = None,
        granularity: str | None = None,
        search_count_fields: list[str] | None = None,
        next_token: str | None = None,
    ) -> PaginatedResult:
        """Get count of recent Posts matching a search query."""
        path = "tweets/counts/recent"
        params = {"query": query}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if since_id:
            params["since_id"] = since_id
        if until_id:
            params["until_id"] = until_id
        if granularity:
            params["granularity"] = granularity
        if search_count_fields:
            params["search_count.fields"] = ",".join(search_count_fields)
        if next_token:
            params["next_token"] = next_token

        res = await self._request("GET", path, params=params, auth_type="bearer_token")

        data = res.get("data", [])
        meta = res.get("meta", {})

        return PaginatedResult(
            data=data,
            next_token=meta.get("next_token"),
            result_count=meta.get("total_tweet_count", len(data)),
        )
