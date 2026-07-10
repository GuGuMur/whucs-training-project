from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.v1.auth import current_user
from app.domain.schemas import FolderCreate, FolderItem, FolderTreeResponse, FolderUpdate, UserPublic
from app.services.workspace import workspace_service

router = APIRouter()


@router.get("/folders/tree", response_model=FolderTreeResponse)
def folders(user: Annotated[UserPublic, Depends(current_user)]) -> FolderTreeResponse:
    return FolderTreeResponse(items=workspace_service.folder_tree(user))


@router.post("/folders", response_model=FolderItem, status_code=status.HTTP_201_CREATED)
def create_folder(payload: FolderCreate, user: Annotated[UserPublic, Depends(current_user)]) -> FolderItem:
    return workspace_service.create_folder(payload, user)


@router.patch("/folders/{folder_id}", response_model=FolderItem)
def update_folder(
    folder_id: str,
    payload: FolderUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FolderItem:
    return workspace_service.update_folder(folder_id, payload, user)


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(folder_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> Response:
    workspace_service.delete_folder(folder_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
