"""
X Media Mixin for uploads and metadata.
"""

import asyncio
from typing import TYPE_CHECKING, Any

from socialconnector.core.exceptions import MediaError, SocialConnectorError

from .models import (
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
    UploadRequest,
    UploadResponse,
)

if TYPE_CHECKING:
    import logging

    class XMediaMixinProtocol:
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

    class XMediaMixinProtocol:
        pass


class XMediaMixin(XMediaMixinProtocol):
    """Mixin for X Media API operations (upload, metadata, analytics)."""

    async def get_media_by_key(self, media_key: str, media_fields: list[str] | None = None) -> GetByKeyResponse:
        """
        Get media by key
        Returns details of a specific media by its media_key.
        """
        path = f"media/{self._validate_path_param('media_key', media_key)}"
        params: dict[str, Any] = {}
        if media_fields is not None:
            params["media.fields"] = ",".join(media_fields)

        res = await self._request("GET", path, params=params, auth_type="oauth2")
        return GetByKeyResponse.model_validate(res)

    async def get_media_by_keys(
        self, media_keys: list[str], media_fields: list[str] | None = None
    ) -> GetByKeysResponse:
        """
        Get media by keys
        Returns details of multiple media by their media_keys.
        """
        path = "media"
        params: dict[str, Any] = {"media_keys": ",".join(media_keys)}
        if media_fields is not None:
            params["media.fields"] = ",".join(media_fields)

        res = await self._request("GET", path, params=params, auth_type="oauth2")
        return GetByKeysResponse.model_validate(res)

    async def get_media_analytics(
        self,
        media_keys: list[str],
        start_time: str | None = None,
        end_time: str | None = None,
        granularity: str | None = None,
        media_analytics_fields: list[str] | None = None,
    ) -> GetAnalyticsResponse:
        """
        Get media analytics
        Returns analytics data for specific media_keys.
        """
        path = "media/analytics"
        params: dict[str, Any] = {"media_keys": ",".join(media_keys)}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if granularity:
            params["granularity"] = granularity
        if media_analytics_fields:
            params["media_analytics.fields"] = ",".join(media_analytics_fields)

        res = await self._request("GET", path, params=params, auth_type="oauth2")
        return GetAnalyticsResponse.model_validate(res)

    async def _upload_media(self, media: Any) -> str:
        """
        Legacy helper for tests.
        """
        return await self.upload_media(media.file_bytes, media.mime_type, media.type.name.lower())

    async def upload_media(self, media_bytes: bytes, media_type: str, media_category: str = "tweet_image") -> str:
        """
        High-level helper to upload media to X.
        Handles INIT, APPEND, and FINALIZE steps.
        """
        # 1. INIT
        init_res = await self.initialize_upload(
            InitializeUploadRequest(total_bytes=len(media_bytes), media_type=media_type, media_category=media_category)
        )
        media_id = init_res.data.id if init_res.data else None
        if not media_id:
            raise SocialConnectorError("Failed to initialize media upload", platform="x")

        # 2. APPEND (Chunked upload)
        chunk_size = 1024 * 1024  # 1MB chunks
        for i in range(0, len(media_bytes), chunk_size):
            segment_index = i // chunk_size
            chunk = media_bytes[i : i + chunk_size]
            await self.append_upload(media_id, chunk, segment_index)

        # 3. FINALIZE
        await self.finalize_upload(media_id)

        return media_id

    MAX_POLL_ATTEMPTS = 5

    async def _poll_media_status(
        self, media_id: str, processing_info: FinalizeUploadResponseDataProcessingInfo
    ) -> GetUploadStatusResponse:
        """Helper to poll media processing status until complete or failed."""
        state = processing_info.state
        attempts = 0
        while state in ["pending", "in_progress"]:
            attempts += 1
            if attempts > self.MAX_POLL_ATTEMPTS:
                raise MediaError("media polling exceeded max attempts", platform="x")

            check_after = processing_info.check_after_secs or 5
            if check_after > 0:
                await asyncio.sleep(check_after)

            status_res = await self.get_upload_status(media_id)
            if not status_res.data or not status_res.data.processing_info:
                return status_res

            state = status_res.data.processing_info.state
            processing_info = status_res.data.processing_info
            if state == "failed":
                raise SocialConnectorError("Media processing failed", platform="x")

        return await self.get_upload_status(media_id)

    async def initialize_upload(self, body: InitializeUploadRequest) -> InitializeUploadResponse:
        """INIT step of media upload."""
        path = "media/upload/initialize"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("POST", path, json=json_data, auth_type="oauth1")
        return InitializeUploadResponse.model_validate(res)

    async def append_upload(self, media_id: str, media_chunk: bytes, segment_index: int) -> AppendUploadResponse:
        """APPEND step of media upload."""
        m_id = self._validate_path_param("media_id", media_id)
        path = f"media/upload/{m_id}/append"
        files = {"media": ("blob", media_chunk)}
        data = {"command": "APPEND", "media_id": m_id, "segment_index": str(segment_index)}
        res = await self._request("POST", path, data=data, files=files, auth_type="oauth1")
        return AppendUploadResponse.model_validate(res)

    async def finalize_upload(self, media_id: str) -> FinalizeUploadResponse:
        """FINALIZE step of media upload."""
        m_id = self._validate_path_param("media_id", media_id)
        path = f"media/upload/{m_id}/finalize"
        data = {"command": "FINALIZE", "media_id": m_id}
        res = await self._request("POST", path, data=data, auth_type="oauth1")
        return FinalizeUploadResponse.model_validate(res)

    async def get_upload_status(self, media_id: str) -> GetUploadStatusResponse:
        """STATUS step of media upload."""
        m_id = self._validate_path_param("media_id", media_id)
        path = "media/upload"
        params = {"command": "STATUS", "media_id": m_id}
        res = await self._request("GET", path, params=params, auth_type="oauth1")
        return GetUploadStatusResponse.model_validate(res)

    async def upload(self, body: UploadRequest) -> UploadResponse:
        """Initiate simplified upload."""
        path = "media/upload"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("POST", path, json=json_data, auth_type="oauth1")
        return UploadResponse.model_validate(res)

    async def create_metadata(self, body: CreateMetadataRequest) -> CreateMetadataResponse:
        """Create media metadata (e.g., alt text)."""
        path = "media/metadata"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("POST", path, json=json_data, auth_type="oauth1")
        return CreateMetadataResponse.model_validate(res)

    async def create_subtitles(self, body: CreateSubtitlesRequest) -> CreateSubtitlesResponse:
        """Create media subtitles."""
        path = "media/subtitles"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("POST", path, json=json_data, auth_type="oauth1")
        return CreateSubtitlesResponse.model_validate(res)

    async def delete_subtitles(self, body: DeleteSubtitlesRequest) -> DeleteSubtitlesResponse:
        """Delete media subtitles."""
        path = "media/subtitles"
        json_data = body.model_dump(exclude_none=True)
        res = await self._request("DELETE", path, json=json_data, auth_type="oauth1")
        return DeleteSubtitlesResponse.model_validate(res)
