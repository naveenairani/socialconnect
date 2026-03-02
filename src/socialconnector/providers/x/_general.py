"""
X General API Mixin for OpenAPI specification retrieval.
"""


from typing import TYPE_CHECKING, Any

from socialconnector.core.models import GetOpenApiSpecResponse

if TYPE_CHECKING:
    import logging

    class XGeneralMixinProtocol:
        logger: logging.Logger
        http_client: Any
        bearer_token_manager: Any
        auth_strategy: str
        auth: Any
        config: Any
        BASE_URL: str
        _request: Any
        _paginate: Any
        _emit: Any
        _validate_path_param: Any
        _get_oauth2_user_token: Any
        _invalidate_oauth2_user_token: Any
else:
    class XGeneralMixinProtocol:
        pass



class XGeneralMixin(XGeneralMixinProtocol):
    """Mixin for X General API operations (OpenAPI Spec)."""

    async def get_open_api_spec(self) -> GetOpenApiSpecResponse:
        """
        Get OpenAPI Spec.
        Retrieves the full OpenAPI Specification in JSON format.
        """
        path = "openapi.json"

        res = await self._request("GET", path, auth_type="oauth2_app")
        return GetOpenApiSpecResponse.model_validate(res)
