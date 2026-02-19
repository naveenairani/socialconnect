"""
X Compliance Mixin for batch compliance jobs.
"""

import os
from typing import Any

from socialconnector.core.exceptions import SocialConnectorError


class XComplianceMixin:
    """Mixin for X Batch Compliance API v2."""

    async def create_compliance_job(self, type: str, name: str) -> dict[str, Any]:
        """
        Create a new compliance job (tweets or users).
        Endpoint: POST /2/compliance/jobs
        """
        path = "compliance/jobs"
        data = {"type": type, "name": name}
        # Compliance jobs use Bearer Token (App-only)
        res = await self._request("POST", path, json=data, auth_type="oauth2")
        return res.get("data", {})

    async def list_compliance_jobs(
        self, type: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get a list of compliance jobs.
        Endpoint: GET /2/compliance/jobs
        """
        path = "compliance/jobs"
        params = {}
        if type:
            params["type"] = type
        if status:
            params["status"] = status

        res = await self._request("GET", path, params=params, auth_type="oauth2")
        return res.get("data", [])

    async def get_compliance_job(self, job_id: str) -> dict[str, Any]:
        """
        Get details for a single compliance job.
        Endpoint: GET /2/compliance/jobs/:id
        """
        path = f"compliance/jobs/{job_id}"
        res = await self._request("GET", path, auth_type="oauth2")
        return res.get("data", {})

    async def upload_compliance_ids(self, upload_url: str, file_path: str) -> bool:
        """
        Upload IDs for a compliance job using a pre-signed URL.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ID file not found: {file_path}")

        headers = {"Content-Type": "text/plain"}
        try:
            with open(file_path, "rb") as f:
                # Direct PUT to upload_url (external to X API v2 base URL)
                response = await self.http_client.request(
                    "PUT", upload_url, content=f.read(), headers=headers
                )
                response.raise_for_status()
                return True
        except Exception as e:
            self.logger.error(f"Failed to upload compliance IDs: {e}")
            raise SocialConnectorError(f"Upload failed: {e}", platform="x") from e

    async def download_compliance_results(self, download_url: str) -> str:
        """
        Download results from a compliance job using a pre-signed URL.
        Returns the raw text content.
        """
        try:
            # Direct GET to download_url (external to X API v2 base URL)
            response = await self.http_client.request("GET", download_url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Failed to download compliance results: {e}")
            raise SocialConnectorError(f"Download failed: {e}", platform="x") from e
