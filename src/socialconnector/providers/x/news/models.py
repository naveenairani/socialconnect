from typing import Any

from pydantic import BaseModel, ConfigDict


class NewsSearchResponseData(BaseModel):
    id: str | None = None
    title: str | None = None
    abstract: str | None = None
    author_id: str | None = None
    created_at: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class NewsSearchResponse(BaseModel):
    data: list[NewsSearchResponseData] | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class NewsGetResponse(BaseModel):
    data: NewsSearchResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")
