from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CommunityNote(BaseModel):
    """Community Note model"""

    id: str | None = None
    text: str | None = None
    created_at: str | None = None
    user_id: str | None = None
    tweet_id: str | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class DeleteResponse(BaseModel):
    """Note deletion response"""

    success: bool
    raw: dict[str, Any] = Field(default_factory=dict)
