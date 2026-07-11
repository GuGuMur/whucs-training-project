from datetime import datetime
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from app.api.v2._deps import get_svc, current_user
from app.domain.schemas import (
    FileAnnotationCreate,
    FileAnnotationItem,
    FileAnnotationListResponse,
    FileAnnotationReplyCreate,
    FileAnnotationReplyItem,
    CompressionRequest,
    CompressionResult,
    FileContentResponse,
    FileContentUpdate,
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
    ShareLinkPublic,
    UserPublic,
)
from app.services.workspace_db import WorkspaceServiceDB

router = APIRouter()


@router.get("/files", response_model=FileListResponse)
async def list_files(
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
    query: str | None = None,
    tag: str | None = None,
    file_type: str | None = None,
    updated_from: datetime | None = None,
    updated_to: datetime | None = None,
) -> FileListResponse:
    items = await svc.list_files(user)
    if query:
        items = [item for item in items if query.lower() in item.name.lower()]
    if tag:
        items = [item for item in items if tag in item.tags]
    if file_type:
        items = [item for item in items if item.type == file_type]
    if updated_from:
        items = [item for item in items if item.updated_at >= updated_from]
    if updated_to:
        items = [item for item in items if item.updated_at <= updated_to]
    return FileListResponse(items=items, total=len(items))


@router.post("/files/upload", response_model=FileItem, status_code=status.HTTP_201_CREATED)
async def upload_file(
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
    file: Annotated[UploadFile, File()] = None,
    folder_id: Annotated[str, Form()] = "",
    tags: Annotated[str | None, Form()] = None,
) -> FileItem:
    content = await file.read()
    return await svc.upload_file(
        file.filename or "unnamed", folder_id, content,
        (tags or "").split(",") if tags else [], user,
    )


@router.patch("/files/{file_id}", response_model=FileItem)
async def update_file(
    file_id: str,
    payload: FileUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FileItem:
    return await svc.update_file(file_id, payload, user)


@router.post("/files/{file_id}/copy", response_model=FileItem, status_code=status.HTTP_201_CREATED)
async def copy_file(
    file_id: str,
    payload: FileCopyRequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FileItem:
    return await svc.copy_file(file_id, payload, user)


@router.post("/files/{file_id}/reparse", response_model=FileItem)
async def reparse_file(
    file_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FileItem:
    return await svc.reparse_file(file_id, user)

@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> Response:
    await svc.delete_file(file_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> Response:
    file_item, content = await svc.download_file(file_id, user)
    encoded_name = quote(file_item.name, safe="")
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"},
    )


@router.get("/files/{file_id}/content", response_model=FileContentResponse)
async def file_content(
    file_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FileContentResponse:
    return await svc.read_file_content_text(file_id, user)


@router.patch("/files/{file_id}/content", response_model=FileItem)
async def update_file_content(
    file_id: str,
    payload: FileContentUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FileItem:
    return await svc.update_file_content_text(file_id, payload, user)


@router.get("/files/recycle-bin", response_model=RecycleBinResponse)
async def recycle_bin(
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> RecycleBinResponse:
    items = await svc.list_deleted_files(user)
    return RecycleBinResponse(items=items, total=len(items))


@router.post("/files/{file_id}/restore", response_model=FileItem)
async def restore_deleted_file(
    file_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FileItem:
    return await svc.restore_deleted_file(file_id, user)


@router.post("/files/{file_id}/share-links", response_model=ShareLinkPublic, status_code=status.HTTP_201_CREATED)
async def create_file_share_link(
    file_id: str,
    payload: ShareLinkCreateRequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> ShareLinkPublic:
    return await svc.create_share_link(file_id, payload, user)


@router.get("/files/{file_id}/versions", response_model=FileVersionListResponse)
async def file_versions(
    file_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FileVersionListResponse:
    return FileVersionListResponse(items=await svc.list_file_versions(file_id, user))


@router.post("/files/{file_id}/versions/{version_id}/restore", response_model=FileItem)
async def restore_file_version(
    file_id: str,
    version_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FileItem:
    return await svc.restore_file_version(file_id, version_id, user)


@router.get("/files/{file_id}/annotations", response_model=FileAnnotationListResponse)
async def file_annotations(
    file_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FileAnnotationListResponse:
    items = await svc.list_file_annotations(file_id, user)
    return FileAnnotationListResponse(items=items, total=len(items))


@router.post(
    "/files/{file_id}/annotations",
    response_model=FileAnnotationItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_file_annotation(
    file_id: str,
    payload: FileAnnotationCreate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FileAnnotationItem:
    return await svc.create_file_annotation(file_id, payload, user)


@router.post(
    "/annotations/{annotation_id}/replies",
    response_model=FileAnnotationReplyItem,
    status_code=status.HTTP_201_CREATED,
)
async def reply_file_annotation(
    annotation_id: str,
    payload: FileAnnotationReplyCreate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FileAnnotationReplyItem:
    return await svc.reply_file_annotation(annotation_id, payload, user)


@router.delete("/files/{file_id}/annotations/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_annotation(
    file_id: str,
    annotation_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> Response:
    await svc.delete_file_annotation(file_id, annotation_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/files/multipart-uploads",
    response_model=MultipartUploadSession,
    status_code=status.HTTP_201_CREATED,
)
async def init_multipart_upload(
    payload: MultipartUploadInitRequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> MultipartUploadSession:
    return await svc.init_multipart_upload(payload, user)


@router.get("/files/multipart-uploads/{session_id}", response_model=MultipartUploadSession)
async def multipart_upload_status(
    session_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> MultipartUploadSession:
    return await svc.get_multipart_upload(session_id, user)


@router.put(
    "/files/multipart-uploads/{session_id}/chunks/{chunk_index}",
    response_model=MultipartChunkResponse,
)
async def upload_multipart_chunk(
    session_id: str,
    chunk_index: int,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
    chunk: Annotated[UploadFile, File()] = None,
    sha256: Annotated[str, Form()] = "",
) -> MultipartChunkResponse:
    chunk_data = await chunk.read()
    return await svc.upload_multipart_chunk(session_id, chunk_index, chunk_data, sha256, user)


@router.post(
    "/files/multipart-uploads/{session_id}/complete",
    response_model=FileItem,
    status_code=status.HTTP_201_CREATED,
)
async def complete_multipart_upload(
    session_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FileItem:
    return await svc.complete_multipart_upload(session_id, user)


@router.post("/files/compress", response_model=CompressionResult, status_code=status.HTTP_201_CREATED)
async def compress_files(
    payload: CompressionRequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> CompressionResult:
    return await svc.compress_files(payload.file_ids, payload.algorithm, user)


@router.post("/files/{file_id}/decompress", response_model=list[CompressionResult], status_code=status.HTTP_201_CREATED)
async def decompress_file(
    file_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> list[CompressionResult]:
    return await svc.decompress_file(file_id, user)
