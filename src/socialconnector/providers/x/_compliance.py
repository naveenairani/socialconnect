"""
X Compliance Mixin for batch compliance jobs.
"""

import tempfile
from pathlib import Path
from urllib.parse import urlparse

from socialconnector.core.exceptions import SocialConnectorError
from socialconnector.core.models import (
    CreateJobsRequest,
    CreateJobsResponse,
    GetJobsByIdResponse,
    GetJobsResponse,
)


class XComplianceMixin:
    """Mixin for X Batch Compliance API v2."""

    def _validate_compliance_url(self, url: str) -> str:
        """SSRF Protection: Validate that compliance URLs are on allowed domains."""
        sanitized = url.strip()
        parsed = urlparse(sanitized)
        if parsed.scheme != "https":
            raise SocialConnectorError(f"Insecure protocol in compliance URL: {sanitized}", platform="x")

        # Allow official X API hosts and AWS pre-signed URLs only.
        domain = (parsed.hostname or "").lower()
        trusted_x_domains = {"api.x.com", "api.twitter.com"}
        is_x_domain = domain in trusted_x_domains
        is_aws_presigned = domain == "amazonaws.com" or domain.endswith(".amazonaws.com")
        if not (is_x_domain or is_aws_presigned):
            raise SocialConnectorError(f"Blocked untrusted compliance URL: {sanitized}", platform="x")

        return sanitized

    def _safe_path(self, file_path: str) -> Path:
        """Path Traversal Protection: Resolve path and ensure it's within CWD or Temp."""
        p = Path(file_path).resolve()
        cwd = Path.cwd().resolve()
        tmp = Path(tempfile.gettempdir()).resolve()
        if not (p.is_relative_to(cwd) or p.is_relative_to(tmp)):
            raise SocialConnectorError(f"Path traversal detected: {file_path}", platform="x")
        return p

    async def create_compliance_job(self, body: CreateJobsRequest) -> CreateJobsResponse:
        """
        Create a new compliance job (tweets or users).
        Endpoint: POST /2/compliance/jobs
        """
        path = "compliance/jobs"
        data = body.model_dump(exclude_none=True)
        # Compliance jobs use Bearer Token (App-only)
        res = await self._request("POST", path, json=data, auth_type="oauth2")
        return CreateJobsResponse.model_validate(res)

    async def list_compliance_jobs(
        self, type: str | None = None, status: str | None = None
    ) -> GetJobsResponse:
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
        return GetJobsResponse.model_validate(res)

    async def get_compliance_job(self, job_id: str) -> GetJobsByIdResponse:
        """
        Get details for a single compliance job.
        Endpoint: GET /2/compliance/jobs/:id
        """
        path = f"compliance/jobs/{self._validate_path_param('job_id', job_id)}"
        res = await self._request("GET", path, auth_type="oauth2")
        return GetJobsByIdResponse.model_validate(res)

    async def upload_compliance_ids(self, upload_url: str, file_path: str) -> bool:
        """
        Upload IDs for a compliance job using a pre-signed URL.
        """
        safe_url = self._validate_compliance_url(upload_url)
        safe_file = self._safe_path(file_path)

        if not safe_file.exists():
            raise FileNotFoundError(f"ID file not found: {safe_file}")

        headers = {"Content-Type": "text/plain"}
        try:
            with open(safe_file, "rb") as f:
                # Direct PUT to upload_url (external to X API v2 base URL)
                response = await self.http_client.request(
                    "PUT", safe_url, content=f.read(), headers=headers
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
        safe_url = self._validate_compliance_url(download_url)
        try:
            # Direct GET to download_url (external to X API v2 base URL)
            response = await self.http_client.request("GET", safe_url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Failed to download compliance results: {e}")
            raise SocialConnectorError(f"Download failed: {e}", platform="x") from e
