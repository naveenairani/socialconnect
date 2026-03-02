from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ComplianceJobData(BaseModel):
    created_at: str | None = None
    download_expires_at: str | None = None
    download_url: str | None = None
    id: str | None = None
    name: str | None = None
    status: str | None = None
    type: str | None = None
    upload_expires_at: str | None = None
    upload_url: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetJobsByIdResponse(BaseModel):
    data: ComplianceJobData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetJobsResponseMeta(BaseModel):
    result_count: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class GetJobsResponse(BaseModel):
    data: list[ComplianceJobData] | None = None
    errors: list[Any] | None = None
    meta: GetJobsResponseMeta | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CreateJobsRequest(BaseModel):
    type: str = Field(..., description="Type of compliance job.")
    name: str | None = None
    resumable: bool | None = None

    model_config = ConfigDict(populate_by_name=True)


class CreateJobsResponse(BaseModel):
    data: ComplianceJobData | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")
