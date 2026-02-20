"""
X Tweets Mixin for managing posts, timelines, and searches.
"""

from typing import Any

from socialconnector.core.exceptions import MessageError
from socialconnector.core.models import Media, MessageResponse, PaginatedResult, Tweet


class XTweetsMixin:
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

    async def delete_message(self, chat_id: str, message_id: str) -> bool:
        """Delete a tweet."""
        self.logger.info(f"Deleting tweet: {message_id}")
        try:
            await self._request("DELETE", f"tweets/{self._validate_path_param('message_id', message_id)}", auth_type="oauth1")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete tweet {message_id}: {e}")
            return False

    async def get_tweet(self, tweet_id: str) -> Tweet:
        """Get a single tweet by ID."""
        params = {
            "tweet.fields": "author_id,created_at,conversation_id,in_reply_to_user_id,referenced_tweets,public_metrics"
        }
        res = await self._request("GET", f"tweets/{self._validate_path_param('tweet_id', tweet_id)}", params=params)
        data = res.get("data", {})
        return Tweet(**data, raw=res)

    async def get_tweets(self, ids: list[str]) -> list[Tweet]:
        """Get multiple tweets by IDs."""
        params = {
            "ids": ",".join(ids),
            "tweet.fields": "author_id,created_at,conversation_id,in_reply_to_user_id,referenced_tweets,public_metrics",
        }
        res = await self._request("GET", "tweets", params=params)
        data = res.get("data", [])
        return [Tweet(**tweet, raw=res) for tweet in data]

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

    async def get_list_tweets(self, list_id: str, *, limit: int = 50) -> PaginatedResult:
        """Get tweets from a list."""
        path = f"lists/{self._validate_path_param('list_id', list_id)}/tweets"
        return await self._paginate(path, limit=limit)

    async def search_tweets(self, query: str, *, limit: int = 50, all_history: bool = False) -> PaginatedResult:
        """Search for tweets. all_history=True requires Academic/Pro tier."""
        path = "tweets/search/all" if all_history else "tweets/search/recent"
        params = {
            "query": query,
            "tweet.fields": "author_id,created_at,conversation_id,in_reply_to_user_id,referenced_tweets,public_metrics",
        }
        return await self._paginate(path, params, limit=limit)
