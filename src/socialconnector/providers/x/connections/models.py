from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DeleteAllResponseData(BaseModel):
    failed_kills: int | None = None
    results: list[Any] | None = None
    successful_kills: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class DeleteAllResponse(BaseModel):
    data: DeleteAllResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetConnectionHistoryResponseMeta(BaseModel):
    next_token: str | None = None
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetConnectionHistoryResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    meta: GetConnectionHistoryResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class DeleteByUuidsRequest(BaseModel):
    uuids: list[str] = Field(..., description="Array of connection UUIDs to terminate")

    model_config = ConfigDict(populate_by_name=True)


class DeleteByUuidsResponseData(BaseModel):
    failed_kills: int | None = None
    results: list[Any] | None = None
    successful_kills: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class DeleteByUuidsResponse(BaseModel):
    data: DeleteByUuidsResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class DeleteByEndpointResponseData(BaseModel):
    failed_kills: int | None = None
    results: list[Any] | None = None
    successful_kills: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class DeleteByEndpointResponse(BaseModel):
    data: DeleteByEndpointResponseData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")
