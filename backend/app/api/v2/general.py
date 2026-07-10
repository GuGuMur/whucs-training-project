from typing import Annotated
from fastapi import APIRouter, Depends
from app.domain.schemas import WorkspaceSnapshot, UserPublic
from app.services.workspace_db import WorkspaceServiceDB
from app.api.v2._deps import get_svc, current_user

router = APIRouter()

@router.get("/workspace/snapshot", response_model=WorkspaceSnapshot)
async def workspace_snapshot(user: Annotated[UserPublic, Depends(current_user)], svc: WorkspaceServiceDB = Depends(get_svc)) -> WorkspaceSnapshot:
    return await svc.snapshot(user)

@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "backend": "db"}
