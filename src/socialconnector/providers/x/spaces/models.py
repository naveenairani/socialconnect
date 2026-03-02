from typing import Any

from pydantic import BaseModel, ConfigDict


class SpaceSearchResponseMeta(BaseModel):
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class SpaceSearchResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: SpaceSearchResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class SpaceGetBuyersResponseMeta(BaseModel):
    next_token: str | None = None
    previous_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class SpaceGetBuyersResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: SpaceGetBuyersResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class SpaceGetByCreatorIdsResponseMeta(BaseModel):
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class SpaceGetByCreatorIdsResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: SpaceGetByCreatorIdsResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class SpaceGetByIdResponse(BaseModel):
    data: Any | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class SpaceGetByIdsResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class SpaceGetPostsResponseMeta(BaseModel):
    next_token: str | None = None
    previous_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class SpaceGetPostsResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: SpaceGetPostsResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")
