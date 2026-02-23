"""
X Media Mixin for chunked uploads to the v2 media/upload endpoint.
"""

import asyncio
from typing import Any

from socialconnector.core.exceptions import MediaError
from socialconnector.core.models import Media


class XMediaMixin:
    """Mixin for uploading media to X using the v2 chunked upload API."""

    MEDIA_UPLOAD_URL = "https://api.x.com/2/media/upload"
    MAX_POLL_ATTEMPTS = 30

    async def _upload_media(self, media: Media) -> str:
        """Upload media using v2 chunked upload (INIT, APPEND, FINALIZE)."""
        if not media.file_bytes:
            raise MediaError("No file bytes provided for upload", platform="x")

        # INIT
        init_params = {
            "command": "INIT",
            "total_bytes": len(media.file_bytes),
            "media_type": media.mime_type or "image/jpeg",
        }
        # v2 media upload often requires OAuth1 (user context)
        res = await self._request("POST", self.MEDIA_UPLOAD_URL, params=init_params, auth_type="oauth1")
        media_id = res["data"]["id"]

        # APPEND (chunking)
        chunk_size = 1024 * 1024  # 1MB chunks
        for i in range(0, len(media.file_bytes), chunk_size):
            chunk = media.file_bytes[i : i + chunk_size]
            append_params = {
                "command": "APPEND",
                "media_id": media_id,
                "segment_index": i // chunk_size,
            }
            # The 'media' field in multipart should contain the raw bytes
            # In httpx, we can pass data and files.
            # v2 docs for media/upload APPEND expect media as a form field
            files = {"media": ("blob", chunk, media.mime_type)}
            await self._request("POST", self.MEDIA_UPLOAD_URL, data=append_params, files=files, auth_type="oauth1")

        # FINALIZE
        final_params = {"command": "FINALIZE", "media_id": media_id}
        res = await self._request("POST", self.MEDIA_UPLOAD_URL, params=final_params, auth_type="oauth1")

        # Check for processing_info (common for videos)
        processing_info = res.get("data", {}).get("processing_info")
        if processing_info:
            await self._poll_media_status(media_id, processing_info)

        return media_id

    async def _poll_media_status(self, media_id: str, processing_info: dict[str, Any]) -> None:
        """Poll the status of a media upload until it completes"""
        state = processing_info.get("state")
        attempts = 0

        try:
            async with asyncio.timeout(300):  # 5 minute hard cap
                while state in ["pending", "in_progress"]:
                    attempts += 1
                    if attempts > self.MAX_POLL_ATTEMPTS:
                        raise MediaError(f"Media {media_id} polling exceeded max attempts", platform="x")

                    check_after_secs = processing_info.get("check_after_secs", 1)
                    await asyncio.sleep(check_after_secs)

                    status_params = {"command": "STATUS", "media_id": media_id}
                    res = await self._request("GET", self.MEDIA_UPLOAD_URL, params=status_params, auth_type="oauth1")

                    # Check for error
                    new_info = res.get("data", {}).get("processing_info") or res.get("processing_info", {})
                    if new_info:
                        state = new_info.get("state", state)

                    if state == "failed":
                        error_msg = processing_info.get("error", {}).get("message", "Unknown error")
                        raise MediaError(f"Media processing failed: {error_msg}", platform="x")

                if state != "succeeded":
                    self.logger.warning(f"Media {media_id} completed with unknown state: {state}")
        except asyncio.TimeoutError as e:
            raise MediaError(f"Media {media_id} processing timed out after 5 minutes", platform="x") from e

    async def get_media_by_keys(
        self,
        media_keys: list[str],
        media_fields: list[str] | None = None,
    ) -> dict:
        """
        Get Media by media keys.
        Retrieves details of Media files by their media keys (max 100).
        """
        path = "media"
        p = {
            "media_keys": ",".join(media_keys),
        }
        if media_fields:
            p["media.fields"] = ",".join(media_fields)

        return await self._request("GET", path, params=p)

    async def get_media_analytics(
        self,
        media_keys: list[str],
        *,
        end_time: str | None = None,
        start_time: str | None = None,
        granularity: str | None = None,
        media_analytics_fields: list[str] | None = None,
    ) -> dict:
        """
        Get Media analytics.
        Retrieves analytics data for media.
        """
        path = "media/analytics"
        p = {
            "media_keys": ",".join(media_keys),
        }
        if end_time:
            p["end_time"] = end_time
        if start_time:
            p["start_time"] = start_time
        if granularity:
            p["granularity"] = granularity
        if media_analytics_fields:
            p["media_analytics.fields"] = ",".join(media_analytics_fields)

        return await self._request("GET", path, params=p)

    async def get_media_by_key(
        self,
        media_key: str,
        media_fields: list[str] | None = None,
    ) -> dict:
        """
        Get Media by media key.
        Retrieves details of a specific Media file by its media key.
        """
        path = f"media/{self._validate_path_param('media_key', media_key)}"
        p = {}
        if media_fields:
            p["media.fields"] = ",".join(media_fields)

        return await self._request("GET", path, params=p or None)

    async def append_upload(
        self,
        media_id: str,
        media_chunk: bytes,
        segment_index: int,
    ) -> bool:
        """
        Append Media upload.
        Appends data to a Media upload request.
        """
        path = f"media/upload/{self._validate_path_param('media_id', media_id)}/append"

        data = {
            "command": "APPEND",
            "media_id": media_id,
            "segment_index": segment_index,
        }
        files = {"media": ("blob", media_chunk, "application/octet-stream")}

        # v2 media append endpoint requires oauth1 when using user-context (which media uploads usually require)
        try:
            await self._request("POST", path, data=data, files=files, auth_type="oauth1")
            return True
        except Exception as e:
            self.logger.error(f"Failed to append media chunk: {e}")
            return False

    async def finalize_upload(self, media_id: str) -> dict:
        """
        Finalize Media upload.
        Finalizes a Media upload request.
        """
        path = f"media/upload/{self._validate_path_param('media_id', media_id)}/finalize"

        data = {
            "command": "FINALIZE",
            "media_id": media_id,
        }

        # v2 media finalize endpoint requires oauth1 when using user-context
        res = await self._request("POST", path, data=data, auth_type="oauth1")
        return res.get("data", res)

    async def get_upload_status(
        self,
        media_id: str,
    ) -> dict:
        """
        Get Media upload status.
        Retrieves the status of a Media upload by its ID.
        """
        path = "media/upload"
        p = {
            "command": "STATUS",
            "media_id": media_id,
        }

        # Checking upload status requires oauth1 context
        res = await self._request("GET", path, params=p, auth_type="oauth1")

        # Return processing_info if inside data or at top level, else return full response
        if "data" in res and "processing_info" in res["data"]:
            return res["data"]["processing_info"]
        if "processing_info" in res:
            return res["processing_info"]
        return res.get("data", res)

    async def upload(self, **kwargs: Any) -> dict:
        """
        Upload media.
        Uploads a media file for use in posts or other content.
        """
        path = "media/upload"

        # Upload endpoint requires oauth1 when using user-context
        res = await self._request("POST", path, json=kwargs, auth_type="oauth1")
        return res.get("data", res)

    async def create_metadata(self, **kwargs: Any) -> dict:
        """
        Create Media metadata.
        Creates metadata for a Media file.
        """
        path = "media/metadata"

        # Creating metadata requires oauth1 context
        res = await self._request("POST", path, json=kwargs, auth_type="oauth1")
        return res.get("data", res)

    async def create_subtitles(self, **kwargs: Any) -> dict:
        """
        Create Media subtitles.
        Creates subtitles for a specific Media file.
        """
        path = "media/subtitles"

        # Subtitles endpoint requires oauth1 when using user-context
        res = await self._request("POST", path, json=kwargs, auth_type="oauth1")
        return res.get("data", res)

    async def delete_subtitles(self, **kwargs: Any) -> dict:
        """
        Delete Media subtitles.
        Deletes subtitles for a specific Media file.
        """
        path = "media/subtitles"

        # Subtitles endpoint requires oauth1 when using user-context
        res = await self._request("DELETE", path, json=kwargs, auth_type="oauth1")
        return res.get("data", res)

    async def initialize_upload(self, **kwargs: Any) -> dict:
        """
        Initialize media upload.
        Initializes a media upload.
        """
        path = "media/upload/initialize"

        # Initialize upload endpoint requires oauth1 when using user-context
        res = await self._request("POST", path, json=kwargs, auth_type="oauth1")
        return res.get("data", res)
