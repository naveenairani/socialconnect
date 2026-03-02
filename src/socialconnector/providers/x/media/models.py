from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GetByKeyResponseData(BaseModel):
    height: int | None = None
    media_key: str | None = None
    type: str | None = None
    width: int | None = None
    model_config = ConfigDict(populate_by_name=True)


class GetByKeysResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetAnalyticsResponse(BaseModel):
    data: list[Any] | None = None
    errors: list[Any] | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetByKeyResponse(BaseModel):
    data: GetByKeyResponseData | None = None
    errors: list[Any] | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class AppendUploadRequest(BaseModel):
    media: str | None = Field(default=None, description="The file to upload.")
    segment_index: int | None = None
    model_config = ConfigDict(populate_by_name=True)


class AppendUploadResponseData(BaseModel):
    expires_at: int | None = None
    model_config = ConfigDict(populate_by_name=True)


class AppendUploadResponse(BaseModel):
    data: AppendUploadResponseData | None = None
    errors: list[Any] | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class FinalizeUploadResponseDataProcessingInfo(BaseModel):
    check_after_secs: int | None = None
    progress_percent: int | None = None
    state: str | None = None
    model_config = ConfigDict(populate_by_name=True)


class FinalizeUploadResponseData(BaseModel):
    expires_after_secs: int | None = None
    id: str | None = None
    media_key: str | None = None
    processing_info: FinalizeUploadResponseDataProcessingInfo | None = None
    size: int | None = None
    model_config = ConfigDict(populate_by_name=True)


class FinalizeUploadResponse(BaseModel):
    data: FinalizeUploadResponseData | None = None
    errors: list[Any] | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class GetUploadStatusResponse(BaseModel):
    data: FinalizeUploadResponseData | None = None
    errors: list[Any] | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class UploadRequest(BaseModel):
    media: str = Field(...)
    media_category: str = Field(...)
    additional_owners: list[Any] | None = None
    media_type: str | None = None
    shared: bool | None = None
    model_config = ConfigDict(populate_by_name=True)


class UploadResponse(BaseModel):
    data: FinalizeUploadResponseData | None = None
    errors: list[Any] | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CreateMetadataRequestMetadataPreviewImageMediaKey(BaseModel):
    media: str | None = None
    media_category: str | None = None
    model_config = ConfigDict(populate_by_name=True)


class CreateMetadataRequestMetadataPreviewImage(BaseModel):
    media_key: CreateMetadataRequestMetadataPreviewImageMediaKey | None = None
    model_config = ConfigDict(populate_by_name=True)


class CreateMetadataRequestMetadata(BaseModel):
    alt_text: dict[str, str] | None = None
    preview_image: CreateMetadataRequestMetadataPreviewImage | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CreateMetadataRequest(BaseModel):
    id: str = Field(..., description="The unique identifier of this Media.")
    metadata: CreateMetadataRequestMetadata | None = None
    model_config = ConfigDict(populate_by_name=True)


class CreateMetadataResponse(BaseModel):
    data: dict[str, Any] | None = None
    errors: list[Any] | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class CreateSubtitlesRequestSubtitles(BaseModel):
    display_name: str | None = None
    id: str | None = None
    language_code: str | None = None
    model_config = ConfigDict(populate_by_name=True)


class CreateSubtitlesRequest(BaseModel):
    id: str | None = None
    media_category: str | None = None
    subtitles: CreateSubtitlesRequestSubtitles | None = None
    model_config = ConfigDict(populate_by_name=True)


class CreateSubtitlesResponseData(BaseModel):
    associated_subtitles: list[Any] | None = None
    id: str | None = None
    media_category: str | None = None
    model_config = ConfigDict(populate_by_name=True)


class CreateSubtitlesResponse(BaseModel):
    data: CreateSubtitlesResponseData | None = None
    errors: list[Any] | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class DeleteSubtitlesRequest(BaseModel):
    id: str | None = None
    language_code: str | None = None
    media_category: str | None = None
    model_config = ConfigDict(populate_by_name=True)


class DeleteSubtitlesResponseData(BaseModel):
    deleted: bool | None = None
    model_config = ConfigDict(populate_by_name=True)


class DeleteSubtitlesResponse(BaseModel):
    data: DeleteSubtitlesResponseData | None = None
    errors: list[Any] | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class InitializeUploadRequest(BaseModel):
    additional_owners: list[Any] | None = None
    media_category: str | None = None
    media_type: str | None = None
    shared: bool | None = None
    total_bytes: int | None = None
    model_config = ConfigDict(populate_by_name=True)


class InitializeUploadResponse(BaseModel):
    data: FinalizeUploadResponseData | None = None
    errors: list[Any] | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")
