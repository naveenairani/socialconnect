"""
X Users Mixin for managing user info, follows, likes, and bookmarks.
"""

from socialconnector.core.models import PaginatedResult, UserInfo


class XUsersMixin:
    """Mixin for user-related operations (lookups, follow, like, bookmark, lists)."""

    async def get_user_info(self, user_id: str) -> UserInfo:
        """Get user info."""
        res = await self._request("GET", f"users/{self._validate_path_param('user_id', user_id)}")
        data = res.get("data", {})
        return UserInfo(
            id=data.get("id"), platform="x", username=data.get("username"), display_name=data.get("name"), raw=res
        )

    async def get_user_by_username(self, username: str) -> UserInfo:
        """Get user info by username handle."""
        res = await self._request("GET", f"users/by/username/{self._validate_path_param('username', username)}")
        data = res.get("data", {})
        return UserInfo(
            id=data.get("id"), platform="x", username=data.get("username"), display_name=data.get("name"), raw=res
        )

    async def follow_user(self, user_id: str, target_user_id: str) -> bool:
        """Follow a user."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/following"
        try:
            res = await self._request("POST", path, json={"target_user_id": target_user_id}, auth_type="oauth1")
            return res.get("data", {}).get("following", False)
        except Exception as e:
            self.logger.error(f"Failed to follow user {target_user_id}: {e}")
            return False

    async def unfollow_user(self, user_id: str, target_user_id: str) -> bool:
        """Unfollow a user."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/following/{self._validate_path_param('target_user_id', target_user_id)}"
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
            return res.get("data", {}).get("liked", False)
        except Exception as e:
            self.logger.error(f"Failed to like tweet {tweet_id}: {e}")
            return False

    async def unlike_tweet(self, user_id: str, tweet_id: str) -> bool:
        """Unlike a tweet."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/likes/{self._validate_path_param('tweet_id', tweet_id)}"
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
            return res.get("data", {}).get("retweeted", False)
        except Exception as e:
            self.logger.error(f"Failed to retweet tweet {tweet_id}: {e}")
            return False

    async def unretweet(self, user_id: str, tweet_id: str) -> bool:
        """Unretweet a tweet."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/retweets/{self._validate_path_param('tweet_id', tweet_id)}"
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
            return res.get("data", {}).get("bookmarked", False)
        except Exception as e:
            self.logger.error(f"Failed to bookmark tweet {tweet_id}: {e}")
            return False

    async def remove_bookmark(self, user_id: str, tweet_id: str) -> bool:
        """Remove a bookmark."""
        path = f"users/{self._validate_path_param('user_id', user_id)}/bookmarks/{self._validate_path_param('tweet_id', tweet_id)}"
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

    async def create_list(self, name: str, description: str | None = None, private: bool = False) -> str | None:
        """Create a new list."""
        path = "lists"
        data = {"name": name, "private": private}
        if description:
            data["description"] = description
        try:
            res = await self._request("POST", path, json=data, auth_type="oauth1")
            return res.get("data", {}).get("id")
        except Exception as e:
            self.logger.error(f"Failed to create list {name}: {e}")
            return None

    async def delete_list(self, list_id: str) -> bool:
        """Delete a list."""
        path = f"lists/{self._validate_path_param('list_id', list_id)}"
        try:
            res = await self._request("DELETE", path, auth_type="oauth1")
            return res.get("data", {}).get("deleted", False)
        except Exception as e:
            self.logger.error(f"Failed to delete list {list_id}: {e}")
            return False

    async def add_list_member(self, list_id: str, user_id: str) -> bool:
        """Add a member to a list."""
        path = f"lists/{self._validate_path_param('list_id', list_id)}/members"
        try:
            res = await self._request("POST", path, json={"user_id": user_id}, auth_type="oauth1")
            return res.get("data", {}).get("is_member", False)
        except Exception as e:
            self.logger.error(f"Failed to add user {user_id} to list {list_id}: {e}")
            return False

    async def remove_list_member(self, list_id: str, user_id: str) -> bool:
        """Remove a member from a list."""
        path = f"lists/{self._validate_path_param('list_id', list_id)}/members/{self._validate_path_param('user_id', user_id)}"
        try:
            await self._request("DELETE", path, auth_type="oauth1")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove user {user_id} from list {list_id}: {e}")
            return False
