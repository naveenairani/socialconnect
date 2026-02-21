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
            await self._request("POST", self.MEDIA_UPLOAD_URL, params=append_params, files=files, auth_type="oauth1")

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
                    processing_info = res.get("data", {}).get("processing_info", {})
                    state = processing_info.get("state")

                    if state == "failed":
                        error_msg = processing_info.get("error", {}).get("message", "Unknown error")
                        raise MediaError(f"Media processing failed: {error_msg}", platform="x")

                if state != "succeeded":
                    self.logger.warning(f"Media {media_id} completed with unknown state: {state}")
        except asyncio.TimeoutError as e:
            raise MediaError(f"Media {media_id} processing timed out after 5 minutes", platform="x") from e
