"""
X Notes Mixin for managing Community Notes.
"""
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from socialconnector.core.models import (
    CommunityNote,
    DeleteResponse,
    PaginatedResult,
    Tweet,
)

if TYPE_CHECKING:
    import logging

    class XNotesMixinProtocol:
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
else:
    class XNotesMixinProtocol:
        pass



class XNotesMixin(XNotesMixinProtocol):
    """Mixin for Community Notes operations."""
    async def search_written_notes(
        self,
        test_mode: bool = False,
        limit: int = 50,
        note_fields: list[str] | None = None,
    ) -> PaginatedResult:
        """
        Search for Community Notes Written by the user.
        Args:
            test_mode: If true, return notes written for test.
            limit: Max results to return.
            note_fields: List of fields to display.
        Returns:
            PaginatedResult containing CommunityNote objects.
        """
        path = "notes/search/notes_written"
        params = {"test_mode": str(test_mode).lower()}

        if note_fields:
            params["note.fields"] = ",".join(note_fields)

        # /2/notes/search/notes_written requires OAuth 1.0a or OAuth 2.0 User Context.
        # We default to oauth1 as it's common for user-context write/read in this provider.
        res = await self._paginate(path, params=params, limit=limit, auth_type="oauth1")

        # Convert raw data to CommunityNote objects
        res.data = [CommunityNote(**item) for item in res.data]
        return res

    async def create_note(self, text: str) -> CommunityNote:
        """
        Create a Community Note.
        Args:
            text: The text content of the note.
        Returns:
            The created CommunityNote object.
        """
        path = "notes"
        data = {"text": text}
        # /2/notes POST accepts OAuth 1.0a or OAuth 2.0 User Context.
        res = await self._request("POST", path, json=data, auth_type="oauth1")
        note_data = res.get("data", {})
        return CommunityNote(**note_data, raw=res)

    async def evaluate_note(self, note_id: str, helpful: bool | None = None, rating: str | None = None) -> bool:
        """
        Evaluate a Community Note.

        Args:
            note_id: The ID of the note to evaluate.
            helpful: Whether the note was helpful.
            rating: Rating string (e.g., "helpful", "not_helpful").

        Returns:
            True if successful.
        """
        path = "evaluate_note"
        data: dict[str, Any] = {"note_id": note_id}
        if helpful is not None:
            data["helpful"] = helpful
        if rating:
            data["rating"] = rating

        # Endpoint requires User Context
        res = await self._request("POST", path, json=data, auth_type="oauth1")
        return bool(res.get("data", {}).get("success", True))

    async def search_eligible_posts(
        self,
        test_mode: bool = False,
        limit: int = 50,
        post_selection: str | None = None,
        tweet_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        poll_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        place_fields: list[str] | None = None,
    ) -> PaginatedResult:
        """
        Search for Posts Eligible for Community Notes.

        Args:
            test_mode: If true, return notes for test.
            limit: Max results to return.
            post_selection: Valid values are 'feed_size: small' and 'feed_size: large'.
            tweet_fields: List of Tweet fields to display.
            expansions: List of fields to expand.
            media_fields: List of Media fields to display.
            poll_fields: List of Poll fields to display.
            user_fields: List of User fields to display.
            place_fields: List of Place fields to display.

        Returns:
            PaginatedResult containing Tweet objects (eligible posts).
        """
        path = "notes/search/posts_eligible_for_notes"
        params: dict[str, Any] = {"test_mode": str(test_mode).lower()}

        if post_selection:
            params["post_selection"] = post_selection
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

        # /2/notes/search/posts_eligible_for_notes accepts OAuth 1.0a or OAuth 2.0 User Context.
        res = await self._paginate(path, limit=limit, params=params, auth_type="oauth1")
        res.data = [Tweet(**item) for item in res.data]
        return res

    async def delete_note(self, note_id: str) -> DeleteResponse:
        """
        Delete a Community Note.

        Args:
            note_id: The ID of the note to delete.

        Returns:
            DeleteResponse: Status of the deletion.
        """
        path = f"notes/{self._validate_path_param('note_id', note_id)}"
        res = await self._request("DELETE", path, auth_type="oauth1")
        # Twitter API v2 usually returns {"data": {"deleted": True}}
        success = res.get("data", {}).get("deleted", True)
        return DeleteResponse(success=success, raw=res)





