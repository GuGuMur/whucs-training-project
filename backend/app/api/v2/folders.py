from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.v2._deps import get_svc, current_user
from app.domain.schemas import (
    FolderCreate,
    FolderItem,
    FolderTreeResponse,
    FolderUpdate,
    UserPublic,
)
from app.services.workspace_db import WorkspaceServiceDB

router = APIRouter()


@router.get("/folders/tree", response_model=FolderTreeResponse)
async def folder_tree(
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FolderTreeResponse:
    return FolderTreeResponse(items=await svc.folder_tree(user))


@router.post("/folders", response_model=FolderItem, status_code=status.HTTP_201_CREATED)
async def create_folder(
    payload: FolderCreate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FolderItem:
    return await svc.create_folder(payload, user)


@router.patch("/folders/{folder_id}", response_model=FolderItem)
async def update_folder(
    folder_id: str,
    payload: FolderUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> FolderItem:
    return await svc.update_folder(folder_id, payload, user)


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> Response:
    await svc.delete_folder_tree(folder_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
