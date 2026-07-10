from __future__ import annotations

from datetime import datetime
from urllib.parse import quote
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from app.api.v1.auth import current_user
from app.domain.schemas import (
    FileAnnotationCreate,
    FileAnnotationItem,
    FileAnnotationListResponse,
    FileAnnotationReplyCreate,
    FileAnnotationReplyItem,
    FileCopyRequest,
    FileItem,
    FileListResponse,
    FileUpdate,
    FileVersionListResponse,
    MultipartChunkResponse,
    MultipartUploadInitRequest,
    MultipartUploadSession,
    RecycleBinResponse,
    ShareLinkCreateRequest,
    ShareLinkDownloadRequest,
    ShareLinkPublic,
    UserPublic,
)
from app.services.workspace import workspace_service

router = APIRouter()


@router.get("/files", response_model=FileListResponse)
def files(
    user: Annotated[UserPublic, Depends(current_user)],
    query: str | None = None,
    tag: str | None = None,
    file_type: str | None = None,
    updated_from: datetime | None = None,
    updated_to: datetime | None = None,
) -> FileListResponse:
    items = workspace_service.list_files(
        user,
        query=query,
        tag=tag,
        file_type=file_type,
        updated_from=updated_from,
        updated_to=updated_to,
    )
    return FileListResponse(items=items, total=len(items))


@router.post("/files/upload", response_model=FileItem, status_code=status.HTTP_201_CREATED)
async def upload_file(
    user: Annotated[UserPublic, Depends(current_user)],
    file: Annotated[UploadFile, File()],
    folder_id: Annotated[str, Form()],
    tags: Annotated[str | None, Form()] = None,
) -> FileItem:
    return await workspace_service.upload_file(file, folder_id, tags, user)


@router.post(
    "/files/multipart-uploads",
    response_model=MultipartUploadSession,
    status_code=status.HTTP_201_CREATED,
)
def init_multipart_upload(
    payload: MultipartUploadInitRequest,
    user: Annotated[UserPublic, Depends(current_user)],
) -> MultipartUploadSession:
    return workspace_service.init_multipart_upload(payload, user)


@router.get("/files/multipart-uploads/{session_id}", response_model=MultipartUploadSession)
def multipart_upload_status(
    session_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> MultipartUploadSession:
    return workspace_service.get_multipart_upload(session_id, user)


@router.put("/files/multipart-uploads/{session_id}/chunks/{chunk_index}", response_model=MultipartChunkResponse)
async def upload_multipart_chunk(
    session_id: str,
    chunk_index: int,
    user: Annotated[UserPublic, Depends(current_user)],
    chunk: Annotated[UploadFile, File()],
    sha256: Annotated[str, Form()],
) -> MultipartChunkResponse:
    return await workspace_service.upload_multipart_chunk(session_id, chunk_index, chunk, sha256, user)


@router.post(
    "/files/multipart-uploads/{session_id}/complete",
    response_model=FileItem,
    status_code=status.HTTP_201_CREATED,
)
def complete_multipart_upload(
    session_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FileItem:
    return workspace_service.complete_multipart_upload(session_id, user)


@router.get("/files/recycle-bin", response_model=RecycleBinResponse)
def recycle_bin(user: Annotated[UserPublic, Depends(current_user)]) -> RecycleBinResponse:
    items = workspace_service.list_deleted_files(user)
    return RecycleBinResponse(items=items, total=len(items))


@router.patch("/files/{file_id}", response_model=FileItem)
def update_file(
    file_id: str,
    payload: FileUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FileItem:
    return workspace_service.update_file(file_id, payload, user)


@router.post("/files/{file_id}/copy", response_model=FileItem, status_code=status.HTTP_201_CREATED)
def copy_file(
    file_id: str,
    payload: FileCopyRequest,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FileItem:
    return workspace_service.copy_file(file_id, payload, user)


@router.post("/files/{file_id}/share-links", response_model=ShareLinkPublic, status_code=status.HTTP_201_CREATED)
def create_file_share_link(
    file_id: str,
    payload: ShareLinkCreateRequest,
    user: Annotated[UserPublic, Depends(current_user)],
) -> ShareLinkPublic:
    return workspace_service.create_share_link(file_id, payload, user)


@router.get("/files/{file_id}/annotations", response_model=FileAnnotationListResponse)
def file_annotations(
    file_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FileAnnotationListResponse:
    items = workspace_service.list_file_annotations(file_id, user)
    return FileAnnotationListResponse(items=items, total=len(items))


@router.post(
    "/files/{file_id}/annotations",
    response_model=FileAnnotationItem,
    status_code=status.HTTP_201_CREATED,
)
def create_file_annotation(
    file_id: str,
    payload: FileAnnotationCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FileAnnotationItem:
    return workspace_service.create_file_annotation(file_id, payload, user)


@router.post(
    "/annotations/{annotation_id}/replies",
    response_model=FileAnnotationReplyItem,
    status_code=status.HTTP_201_CREATED,
)
def reply_file_annotation(
    annotation_id: str,
    payload: FileAnnotationReplyCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FileAnnotationReplyItem:
    return workspace_service.reply_file_annotation(annotation_id, payload, user)


@router.delete("/files/{file_id}/annotations/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file_annotation(
    file_id: str,
    annotation_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> Response:
    workspace_service.delete_file_annotation(file_id, annotation_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/files/{file_id}/download")
def download_file(file_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> Response:
    file_item, content = workspace_service.download_file(file_id, user)
    encoded_name = quote(file_item.name, safe="")
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"},
    )


@router.post("/share-links/{token}/download")
def download_shared_file(token: str, payload: ShareLinkDownloadRequest | None = None) -> Response:
    file_item, content = workspace_service.download_shared_file(token, payload.password if payload else None)
    encoded_name = quote(file_item.name, safe="")
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"},
    )


@router.get("/files/{file_id}/versions", response_model=FileVersionListResponse)
def file_versions(file_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> FileVersionListResponse:
    return FileVersionListResponse(items=workspace_service.list_file_versions(file_id, user))


@router.post("/files/{file_id}/versions/{version_id}/restore", response_model=FileItem)
def restore_file_version(
    file_id: str,
    version_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FileItem:
    return workspace_service.restore_file_version(file_id, version_id, user)


@router.post("/files/{file_id}/restore", response_model=FileItem)
def restore_deleted_file(file_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> FileItem:
    return workspace_service.restore_deleted_file(file_id, user)


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> Response:
    workspace_service.delete_file(file_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
