"""
X Connections Mixin for managing streaming connections.
"""

from collections.abc import AsyncGenerator

from socialconnector.core.models import (
    DeleteAllResponse,
    DeleteByEndpointResponse,
    DeleteByUuidsRequest,
    DeleteByUuidsResponse,
    GetConnectionHistoryResponse,
)


class XConnectionsMixin:
    """Mixin for X Connections API v2."""

    async def get_connection_history(
        self,
        status: str | None = None,
        endpoints: list[str] | None = None,
        max_results: int | None = None,
        pagination_token: str | None = None,
        connection_fields: list[str] | None = None,
    ) -> AsyncGenerator[GetConnectionHistoryResponse, None]:
        """
        Get Connection History
        Returns active and historical streaming connections with disconnect reasons for the authenticated application.
        Automatically handles pagination.
        """
        url = "connections"
        current_pagination_token = pagination_token

        while True:
            params = {}
            if status is not None:
                params["status"] = status
            if endpoints is not None:
                params["endpoints"] = ",".join(str(item) for item in endpoints)
            if max_results is not None:
                params["max_results"] = max_results
            if connection_fields is not None:
                params["connection.fields"] = ",".join(str(item) for item in connection_fields)
            if current_pagination_token:
                params["pagination_token"] = current_pagination_token

            res = await self._request("GET", url, params=params, auth_type="bearer_token")
            page_response = GetConnectionHistoryResponse.model_validate(res)
            yield page_response

            next_token = None
            if page_response.meta:
                next_token = page_response.meta.next_token
            elif isinstance(res, dict) and "meta" in res:
                next_token = res["meta"].get("next_token")

            if not next_token:
                break
            current_pagination_token = next_token

    async def delete_all_connections(self) -> DeleteAllResponse:
        """
        Terminate all connections
        Terminates all active streaming connections for the authenticated application.
        """
        url = "connections/all"
        res = await self._request("DELETE", url, auth_type="bearer_token")
        return DeleteAllResponse.model_validate(res)

    async def delete_connections_by_endpoint(self, endpoint_id: str) -> DeleteByEndpointResponse:
        """
        Terminate connections by endpoint
        Terminates all streaming connections for a specific endpoint ID.
        """
        url = f"connections/{self._validate_path_param('endpoint_id', endpoint_id)}"
        res = await self._request("DELETE", url, auth_type="bearer_token")
        return DeleteByEndpointResponse.model_validate(res)

    async def delete_connections_by_uuids(self, body: DeleteByUuidsRequest) -> DeleteByUuidsResponse:
        """
        Terminate multiple connections
        Terminates multiple streaming connections by their UUIDs.
        """
        url = "connections"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("DELETE", url, json=json_data, auth_type="bearer_token")
        return DeleteByUuidsResponse.model_validate(res)
