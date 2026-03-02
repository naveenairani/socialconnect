"""
X Media Mixin for chunked uploads to the v2 media/upload endpoint.
"""

import asyncio

from socialconnector.core.exceptions import MediaError
from socialconnector.core.models import (
    AppendUploadResponse,
    CreateMetadataRequest,
    CreateMetadataResponse,
    CreateSubtitlesRequest,
    CreateSubtitlesResponse,
    DeleteSubtitlesRequest,
    DeleteSubtitlesResponse,
    FinalizeUploadResponse,
    FinalizeUploadResponseDataProcessingInfo,
    GetAnalyticsResponse,
    GetByKeyResponse,
    GetByKeysResponse,
    GetUploadStatusResponse,
    InitializeUploadRequest,
    InitializeUploadResponse,
    Media,
    UploadRequest,
    UploadResponse,
)


class XMediaMixin:
    """Mixin for uploading media to X using the v2 chunked upload API."""

    MEDIA_UPLOAD_URL = "https://api.x.com/2/media/upload"
    MAX_POLL_ATTEMPTS = 30

    async def _upload_media(self, media: Media) -> str:
        """Upload media using v2 chunked upload (INIT, APPEND, FINALIZE)."""
        if not media.file_bytes:
            raise MediaError("No file bytes provided for upload", platform="x")

        # INIT
        init_req = InitializeUploadRequest(
            total_bytes=len(media.file_bytes),
            media_type=media.mime_type or "image/jpeg",
        )
        init_res = await self.initialize_upload(body=init_req)

        if not init_res.data or not init_res.data.id:
            raise MediaError("Failed to initialize media upload, no ID returned", platform="x")
        media_id = init_res.data.id

        # APPEND (chunking)
        chunk_size = 1024 * 1024  # 1MB chunks
        for i in range(0, len(media.file_bytes), chunk_size):
            chunk = media.file_bytes[i : i + chunk_size]
            await self.append_upload(
                media_id=media_id,
                media_chunk=chunk,
                segment_index=i // chunk_size,
            )

        # FINALIZE
        final_res = await self.finalize_upload(media_id=media_id)

        # Check for processing_info (common for videos)
        if final_res.data and final_res.data.processing_info:
            await self._poll_media_status(media_id, final_res.data.processing_info)

        return media_id

    async def _poll_media_status(
        self, media_id: str, processing_info: FinalizeUploadResponseDataProcessingInfo
    ) -> None:
        """Poll the status of a media upload until it completes"""
        state = processing_info.state
        attempts = 0

        try:
            async with asyncio.timeout(300):  # 5 minute hard cap
                while state in ["pending", "in_progress"]:
                    attempts += 1
                    if attempts > self.MAX_POLL_ATTEMPTS:
                        raise MediaError(f"Media {media_id} polling exceeded max attempts", platform="x")

                    check_after_secs = processing_info.check_after_secs or 1
                    await asyncio.sleep(check_after_secs)

                    status_res = await self.get_upload_status(media_id=media_id)

                    if status_res.data and status_res.data.processing_info:
                        state = status_res.data.processing_info.state
                        processing_info = status_res.data.processing_info

                    if state == "failed":
                        error_msg = "Unknown error"
                        if status_res.errors and len(status_res.errors) > 0:
                            error_msg = str(status_res.errors[0])
                        raise MediaError(f"Media processing failed: {error_msg}", platform="x")

                if state != "succeeded":
                    self.logger.warning(f"Media {media_id} completed with unknown state: {state}")
        except asyncio.TimeoutError as e:
            raise MediaError(f"Media {media_id} processing timed out after 5 minutes", platform="x") from e

    async def get_media_by_keys(
        self,
        media_keys: list[str],
        media_fields: list[str] | None = None,
    ) -> GetByKeysResponse:
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

        res = await self._request("GET", path, params=p)
        return GetByKeysResponse.model_validate(res)

    async def get_media_analytics(
        self,
        media_keys: list[str],
        *,
        end_time: str | None = None,
        start_time: str | None = None,
        granularity: str | None = None,
        media_analytics_fields: list[str] | None = None,
    ) -> GetAnalyticsResponse:
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

        res = await self._request("GET", path, params=p, auth_type="oauth2_user_context")
        return GetAnalyticsResponse.model_validate(res)

    async def get_media_by_key(
        self,
        media_key: str,
        media_fields: list[str] | None = None,
    ) -> GetByKeyResponse:
        """
        Get Media by media key.
        Retrieves details of a specific Media file by its media key.
        """
        path = f"media/{self._validate_path_param('media_key', media_key)}"
        p = {}
        if media_fields:
            p["media.fields"] = ",".join(media_fields)

        res = await self._request("GET", path, params=p or None)
        return GetByKeyResponse.model_validate(res)

    async def append_upload(
        self,
        media_id: str,
        media_chunk: bytes,
        segment_index: int,
    ) -> AppendUploadResponse:
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

        res = await self._request("POST", path, data=data, files=files, auth_type="oauth1")
        return AppendUploadResponse.model_validate(res)

    async def finalize_upload(self, media_id: str) -> FinalizeUploadResponse:
        """
        Finalize Media upload.
        Finalizes a Media upload request.
        """
        path = f"media/upload/{self._validate_path_param('media_id', media_id)}/finalize"

        data = {
            "command": "FINALIZE",
            "media_id": media_id,
        }

        res = await self._request("POST", path, data=data, auth_type="oauth1")
        return FinalizeUploadResponse.model_validate(res)

    async def get_upload_status(
        self,
        media_id: str,
    ) -> GetUploadStatusResponse:
        """
        Get Media upload status.
        Retrieves the status of a Media upload by its ID.
        """
        path = "media/upload"
        p = {
            "command": "STATUS",
            "media_id": media_id,
        }

        res = await self._request("GET", path, params=p, auth_type="oauth1")
        return GetUploadStatusResponse.model_validate(res)

    async def upload(self, body: UploadRequest) -> UploadResponse:
        """
        Upload media.
        Uploads a media file for use in posts or other content.
        """
        path = "media/upload"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("POST", path, json=json_data, auth_type="oauth1")
        return UploadResponse.model_validate(res)

    async def create_metadata(self, body: CreateMetadataRequest) -> CreateMetadataResponse:
        """
        Create Media metadata.
        Creates metadata for a Media file.
        """
        path = "media/metadata"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("POST", path, json=json_data, auth_type="oauth1")
        return CreateMetadataResponse.model_validate(res)

    async def create_subtitles(self, body: CreateSubtitlesRequest) -> CreateSubtitlesResponse:
        """
        Create Media subtitles.
        Creates subtitles for a specific Media file.
        """
        path = "media/subtitles"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("POST", path, json=json_data, auth_type="oauth1")
        return CreateSubtitlesResponse.model_validate(res)

    async def delete_subtitles(self, body: DeleteSubtitlesRequest) -> DeleteSubtitlesResponse:
        """
        Delete Media subtitles.
        Deletes subtitles for a specific Media file.
        """
        path = "media/subtitles"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("DELETE", path, json=json_data, auth_type="oauth1")
        return DeleteSubtitlesResponse.model_validate(res)

    async def initialize_upload(self, body: InitializeUploadRequest) -> InitializeUploadResponse:
        """
        Initialize media upload.
        Initializes a media upload.
        """
        path = "media/upload/initialize"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("POST", path, json=json_data, auth_type="oauth1")
        return InitializeUploadResponse.model_validate(res)
