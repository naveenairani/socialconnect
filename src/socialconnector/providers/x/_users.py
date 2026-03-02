"""
X Users Mixin for managing user info, follows, likes, and bookmarks.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Awaitable, cast

from socialconnector.core.models import PaginatedResult, UserInfo

if TYPE_CHECKING:
    import logging

    class XUsersProtocol:
        logger: logging.Logger
        _request: Callable[..., Awaitable[Any]]
        _paginate: Callable[..., Awaitable[PaginatedResult]]
        _validate_path_param: Callable[[str, Any], str]
        _get_oauth2_user_token: Callable[[], Awaitable[Any]]
        _invalidate_oauth2_user_token: Callable[[], None]
else:
    class XUsersProtocol:
        pass


class XUsersMixin(XUsersProtocol):
    """Mixin for user-related operations (lookups, follow, like, bookmark, lists)."""

    async def get_user_info(self, user_id: str) -> UserInfo:
        """Get user info."""
        res = await self._request("GET", f"users/{self._validate_path_param('user_id', user_id)}")
        data = res.get("data", {})
        return UserInfo(
            id=data.get("id"),
            platform="x",
            username=data.get("username"),
            display_name=data.get("name"),
            raw=res,
        )

    async def get_user_by_username(self, username: str) -> UserInfo:
        """Get user info by username handle."""
        res = await self._request("GET", f"users/by/username/{self._validate_path_param('username', username)}")
        data = res.get("data", {})
        return UserInfo(
            id=data.get("id"),
            platform="x",
            username=data.get("username"),
            display_name=data.get("name"),
            raw=res,
        )

    async def follow_user(self, user_id: str, target_user_id: str) -> bool:
        """Follow a user."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/following"
        try:
            res = await self._request("POST", path, json={"target_user_id": target_user_id}, auth_type="oauth1")
            return bool(res.get("data", {}).get("following", False))
        except Exception as e:
            self.logger.error(f"Failed to follow user {target_user_id}: {e}")
            return False

    async def unfollow_user(self, user_id: str, target_user_id: str) -> bool:
        """Unfollow a user."""
        p1 = self._validate_path_param("user_id", user_id)
        p2 = self._validate_path_param("target_user_id", target_user_id)
        path = f"users/{p1}/following/{p2}"
        try:
            await self._request("DELETE", path, auth_type="oauth1")
            return True
        except Exception as e:
            self.logger.error(f"Failed to unfollow user {target_user_id}: {e}")
            return False

    async def get_followers(self, user_id: str, *, limit: int = 50) -> PaginatedResult:
        """Get followers of a user."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/followers"
        return await self._paginate(path, limit=limit)

    async def get_following(self, user_id: str, *, limit: int = 50) -> PaginatedResult:
        """Get users followed by a user."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/following"
        return await self._paginate(path, limit=limit)

    async def like_tweet(self, user_id: str, tweet_id: str) -> bool:
        """Like a tweet."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/likes"
        try:
            res = await self._request("POST", path, json={"tweet_id": tweet_id}, auth_type="oauth1")
            return bool(res.get("data", {}).get("liked", False))
        except Exception as e:
            self.logger.error(f"Failed to like tweet {tweet_id}: {e}")
            return False

    async def unlike_tweet(self, user_id: str, tweet_id: str) -> bool:
        """Unlike a tweet."""
        p1 = self._validate_path_param("user_id", user_id)
        p2 = self._validate_path_param("tweet_id", tweet_id)
        path = f"users/{p1}/likes/{p2}"
        try:
            await self._request("DELETE", path, auth_type="oauth1")
            return True
        except Exception as e:
            self.logger.error(f"Failed to unlike tweet {tweet_id}: {e}")
            return False

    async def get_liked_tweets(self, user_id: str, *, limit: int = 50) -> PaginatedResult:
        """Get tweets liked by a user."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/liked_tweets"
        return await self._paginate(path, limit=limit)

    async def retweet(self, user_id: str, tweet_id: str) -> bool:
        """Retweet a tweet."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/retweets"
        try:
            res = await self._request("POST", path, json={"tweet_id": tweet_id}, auth_type="oauth1")
            return cast(bool, res.get("data", {}).get("retweeted", False))
        except Exception as e:
            self.logger.error(f"Failed to retweet tweet {tweet_id}: {e}")
            return False

    async def unretweet(self, user_id: str, tweet_id: str) -> bool:
        """Unretweet a tweet."""
        p1 = self._validate_path_param("user_id", user_id)
        p2 = self._validate_path_param("tweet_id", tweet_id)
        path = f"users/{p1}/retweets/{p2}"
        try:
            await self._request("DELETE", path, auth_type="oauth1")
            return True
        except Exception as e:
            self.logger.error(f"Failed to unretweet tweet {tweet_id}: {e}")
            return False

    async def bookmark_tweet(self, user_id: str, tweet_id: str) -> bool:
        """Bookmark a tweet."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/bookmarks"
        try:
            res = await self._request("POST", path, json={"tweet_id": tweet_id}, auth_type="oauth1")
            return bool(res.get("data", {}).get("bookmarked", False))
        except Exception as e:
            self.logger.error(f"Failed to bookmark tweet {tweet_id}: {e}")
            return False

    async def remove_bookmark(self, user_id: str, tweet_id: str) -> bool:
        """Remove a bookmark."""
        p1 = self._validate_path_param("user_id", user_id)
        p2 = self._validate_path_param("tweet_id", tweet_id)
        path = f"users/{p1}/bookmarks/{p2}"
        try:
            await self._request("DELETE", path, auth_type="oauth1")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove bookmark {tweet_id}: {e}")
            return False

    async def get_bookmarks(self, user_id: str, *, limit: int = 50) -> PaginatedResult:
        """Get bookmarked tweets for a user."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/bookmarks"
        # Fix Bug #4: pass auth_type="oauth1" as bookmarks require user context
        return await self._paginate(path, limit=limit, auth_type="oauth1")

    async def add_list_member(self, list_id: str, user_id: str) -> bool:
        """Add a member to a list."""
        path = f"lists/{self._validate_path_param('list_id', list_id)}/members"
        try:
            res = await self._request("POST", path, json={"user_id": user_id}, auth_type="oauth1")
            return bool(res.get("data", {}).get("is_member", False))
        except Exception as e:
            self.logger.error(f"Failed to add user {user_id} to list {list_id}: {e}")
            return False

    async def remove_list_member(self, list_id: str, user_id: str) -> bool:
        """Remove a member from a list."""
        p1 = self._validate_path_param("list_id", list_id)
        p2 = self._validate_path_param("user_id", user_id)
        path = f"lists/{p1}/members/{p2}"
        try:
            await self._request("DELETE", path, auth_type="oauth1")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove user {user_id} from list {list_id}: {e}")
            return False

    async def get_list_followers(
        self, list_id: str, *, limit: int = 100,
        user_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        tweet_fields: list[str] | None = None,
    ) -> PaginatedResult:
        """Get followers of a list."""
        path = f"lists/{self._validate_path_param('list_id', list_id)}/followers"
        fields = [
            ("user.fields", user_fields),
            ("expansions", expansions),
            ("tweet.fields", tweet_fields),
        ]
        p = {k: ",".join(v) for k, v in fields if v}
        return await self._paginate(path, params=p or None, limit=limit)

    async def get_list_by_id(
        self, list_id: str,
        list_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        user_fields: list[str] | None = None,
    ) -> dict[Any, Any]:
        """Get a List by its ID."""
        path = f"lists/{self._validate_path_param('list_id', list_id)}"
        fields = [
            ("list.fields", list_fields),
            ("expansions", expansions),
            ("user.fields", user_fields),
        ]
        p = {k: ",".join(v) for k, v in fields if v}
        return cast(dict[Any, Any], await self._request("GET", path, params=p or None))

    async def update_list(
        self,
        list_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        private: bool | None = None,
    ) -> bool:
        """Update a list's metadata."""
        path = f"lists/{self._validate_path_param('list_id', list_id)}"
        data = {k: v for k, v in [("name", name), ("description", description), ("private", private)] if v is not None}
        if not data:
            return True
        try:
            res = await self._request("PUT", path, json=data, auth_type="oauth1")
            return bool(res.get("data", {}).get("updated", False))
        except Exception as e:
            self.logger.error(f"Failed to update list {list_id}: {e}")
            return False

    async def create_list(self, name: str, *, description: str | None = None, private: bool | None = None) -> dict[Any, Any]:
        """Create a new list."""
        data = {k: v for k, v in [("name", name), ("description", description), ("private", private)] if v is not None}
        try:
            res = await self._request("POST", "lists", json=data, auth_type="oauth1")
            return dict(res.get("data", {}))
        except Exception as e:
            self.logger.error(f"Failed to create list '{name}': {e}")
            raise

    async def delete_list(self, list_id: str) -> bool:
        """Delete a list."""
        path = f"lists/{self._validate_path_param('list_id', list_id)}"
        try:
            res = await self._request("DELETE", path, auth_type="oauth1")
            return bool(res.get("data", {}).get("deleted", False))
        except Exception as e:
            self.logger.error(f"Failed to delete list {list_id}: {e}")
            return False
