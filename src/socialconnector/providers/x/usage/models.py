from typing import Any

from pydantic import BaseModel, ConfigDict


class UsageGetResponseData(BaseModel):
    cap_reset_day: int | None = None
    project_cap: str | None = None
    project_id: str | None = None
    project_usage: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class UsageGetResponse(BaseModel):
    data: list[UsageGetResponseData] | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")
