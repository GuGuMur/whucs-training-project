from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v2._deps import get_svc, current_user
from app.domain.schemas import (
    AuthResponse,
    CurrentUserResponse,
    LoginRequest,
    RefreshTokenRequest,
    UserCreate,
    UserPublic,
    UserUpdate,
)
from app.services.workspace_db import WorkspaceServiceDB

router = APIRouter()


@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, svc: WorkspaceServiceDB = Depends(get_svc)) -> AuthResponse:
    try:
        user, at, rt = await svc.register_user(payload)
        return AuthResponse(access_token=at, refresh_token=rt, expires_in=1800, user=user)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(409, detail={"code": str(e), "message": "注册失败"})


@router.post("/auth/login", response_model=AuthResponse)
async def login(payload: LoginRequest, svc: WorkspaceServiceDB = Depends(get_svc)) -> AuthResponse:
    try:
        user, at, rt = await svc.login_user(payload.account, payload.password)
        return AuthResponse(access_token=at, refresh_token=rt, expires_in=1800, user=user)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(401, detail={"code": "INVALID_CREDENTIALS", "message": "用户名或密码不正确"})


@router.post("/auth/refresh", response_model=AuthResponse)
async def refresh(payload: RefreshTokenRequest, svc: WorkspaceServiceDB = Depends(get_svc)) -> AuthResponse:
    try:
        user, at, rt = await svc.refresh_session(payload.refresh_token)
        return AuthResponse(access_token=at, refresh_token=rt, expires_in=1800, user=user)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(401, detail={"code": str(e), "message": "令牌无效或已过期"})


@router.get("/users/me", response_model=CurrentUserResponse)
async def me(user: Annotated[UserPublic, Depends(current_user)]) -> CurrentUserResponse:
    return CurrentUserResponse(user=user)


@router.patch("/users/me", response_model=CurrentUserResponse)
async def update_me(
    payload: UserUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> CurrentUserResponse:
    return CurrentUserResponse(user=await svc.update_user_profile(user.id, payload))
