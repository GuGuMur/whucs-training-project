from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class FileItem(BaseModel):
    id: str
    name: str
    folder_id: str
    type: str
    size: int
    sha256: str
    parse_status: Literal["queued", "parsing", "indexed", "failed"]
    tags: list[str]
    updated_at: datetime
    permission_scope: str
    knowledge_base_ids: list[str]


class FileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    folder_id: str | None = None
    tags: list[str] | None = None


class FileContentResponse(BaseModel):
    file_id: str
    name: str
    type: str
    content: str
    editable: bool
    updated_at: datetime


class FileContentUpdate(BaseModel):
    content: str = Field(max_length=1_000_000)


class FileCopyRequest(BaseModel):
    target_folder_id: str = Field(min_length=1)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    tags: list[str] | None = None


class FileAnnotationCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    position: dict[str, Any] | None = None


class FileAnnotationReplyCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class FileAnnotationReplyItem(BaseModel):
    id: str
    annotation_id: str
    file_id: str
    author_id: int
    author_name: str
    content: str
    created_at: datetime
    updated_at: datetime


class FileAnnotationItem(BaseModel):
    id: str
    file_id: str
    author_id: int
    author_name: str
    content: str
    position: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    replies: list[FileAnnotationReplyItem] = Field(default_factory=list)


class FileAnnotationListResponse(BaseModel):
    items: list[FileAnnotationItem]
    total: int


class ShareLinkCreateRequest(BaseModel):
    password: str | None = Field(default=None, min_length=4, max_length=128)
    expires_in_seconds: int = Field(default=3600, ge=60)
    download_limit: int | None = Field(default=None, ge=1)


class ShareLinkPublic(BaseModel):
    id: str
    file_id: str
    token: str
    url: str
    expires_at: datetime
    download_limit: int | None
    download_count: int
    has_password: bool


class ShareLinkDownloadRequest(BaseModel):
    password: str | None = Field(default=None, min_length=1, max_length=128)


MultipartUploadStatus = Literal["uploading", "completed", "expired"]


class MultipartUploadInitRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    folder_id: str = Field(min_length=1)
    size: int = Field(ge=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    chunk_size: int = Field(ge=1)
    tags: list[str] = Field(default_factory=list)


class MultipartUploadSession(BaseModel):
    id: str
    filename: str
    folder_id: str
    size: int
    sha256: str
    chunk_size: int
    total_chunks: int
    received_chunks: list[int]
    status: MultipartUploadStatus
    expires_at: datetime


class MultipartChunkResponse(BaseModel):
    session_id: str
    chunk_index: int
    received_chunks: list[int]
    total_chunks: int
    status: MultipartUploadStatus


class FileVersionItem(BaseModel):
    id: str
    file_id: str
    version_no: int
    name: str
    size: int
    sha256: str
    created_at: datetime
    created_by: str
    is_current: bool


class FileVersionListResponse(BaseModel):
    items: list[FileVersionItem]


class FileListResponse(BaseModel):
    items: list[FileItem]
    total: int


class RecycleBinItem(BaseModel):
    file: FileItem
    deleted_at: datetime
    deleted_by: str


class RecycleBinResponse(BaseModel):
    items: list[RecycleBinItem]
    total: int


class CompressionRequest(BaseModel):
    file_ids: list[str] = Field(min_length=1, max_length=50)
    algorithm: Literal["zip", "tar.gz"] = "zip"


class CompressionResult(BaseModel):
    file_id: str
    file_name: str
    original_size: int
    compressed_size: int
    algorithm: str
    ratio: float
