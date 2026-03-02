from typing import Any

from pydantic import BaseModel, ConfigDict


class GetByIdsResponseIncludes(BaseModel):
    """Shared includes model for various X responses."""

    media: list[Any] | None = None
    places: list[Any] | None = None
    polls: list[Any] | None = None
    topics: list[Any] | None = None
    tweets: list[Any] | None = None
    users: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetByIdsResponse(BaseModel):
    """Generic response wrapper for multi-ID lookups."""

    data: list[Any] | None = None
    includes: GetByIdsResponseIncludes | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")
