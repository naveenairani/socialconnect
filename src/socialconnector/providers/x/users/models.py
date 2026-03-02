from typing import Any

from pydantic import BaseModel, ConfigDict

# Users module uses UserInfo from core/models.py or custom models if needed.
# For now, we'll use simple models if _users.py doesn't define specific ones
# that were previously in core/models.py but shared.
# Actually, UserInfo is in core/models.py and is a core model.
# If there are any X-specific user models, they would go here.


class XUserResponse(BaseModel):
    data: Any | None = None
    errors: list[Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")
