from pydantic import BaseModel, ConfigDict


class StreamRule(BaseModel):
    """Stream rule model"""

    id: str | None = None
    value: str | None = None
    tag: str | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")
