from typing import Annotated
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.workspace_db import WorkspaceServiceDB
from app.domain.schemas import UserPublic
from fastapi import HTTPException

def get_svc(db: AsyncSession = Depends(get_db)) -> WorkspaceServiceDB:
    return WorkspaceServiceDB(db)

async def current_user(
    authorization: Annotated[str | None, Header()] = None,
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> UserPublic:
    try:
        return await svc.require_user(authorization)
    except ValueError as e:
        code = str(e)
        if code == "AUTH_REQUIRED":
            raise HTTPException(401, detail={"code": code, "message": "请先登录"})
        if code == "TOKEN_EXPIRED":
            raise HTTPException(401, detail={"code": code, "message": "登录已过期，请重新登录"})
        raise HTTPException(401, detail={"code": "INVALID_TOKEN", "message": "登录状态无效"})
