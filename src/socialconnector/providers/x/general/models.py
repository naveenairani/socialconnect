from pydantic import BaseModel, ConfigDict


class GetOpenApiSpecResponse(BaseModel):
    """Response model for get_open_api_spec"""

    model_config = ConfigDict(populate_by_name=True, extra="allow")
