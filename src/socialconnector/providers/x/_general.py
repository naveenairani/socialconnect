"""
X General API Mixin for OpenAPI specification retrieval.
"""

from typing import Any
import urllib.parse

from socialconnector.core.models import GetOpenApiSpecResponse


class XGeneralMixin:
    """Mixin for X General API operations (OpenAPI Spec)."""

    async def get_open_api_spec(self) -> GetOpenApiSpecResponse:
        """
        Get OpenAPI Spec.
        Retrieves the full OpenAPI Specification in JSON format.
        """
        path = "openapi.json"

        res = await self._request("GET", path, auth_type="bearer_token")
        return GetOpenApiSpecResponse.model_validate(res)
