from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GetByIdResponseData(BaseModel):
    created_at: str | None = None
    id: str | None = None
    name: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetByIdResponse(BaseModel):
    data: GetByIdResponseData | dict[str, Any] = Field(
        description="A X Community is a curated group of Posts.", default_factory=dict
    )
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class SearchResponseMeta(BaseModel):
    next_token: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class SearchResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: SearchResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")
