from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from app.domain.schemas import (
    AuthResponse,
    CurrentUserResponse,
    ErrorResponse,
    LoginRequest,
    RefreshTokenRequest,
    UserCreate,
    UserPublic,
    UserUpdate,
)
from app.services.workspace import workspace_service

router = APIRouter()

auth_login_error_responses = {
    401: {"model": ErrorResponse, "description": "Invalid credentials"},
    423: {"model": ErrorResponse, "description": "Account temporarily locked"},
}


def current_user(authorization: Annotated[str | None, Header()] = None) -> UserPublic:
    return workspace_service.require_user(authorization)


@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate) -> AuthResponse:
    user, access_token, refresh_token = workspace_service.register_user(payload)
    return AuthResponse(access_token=access_token, refresh_token=refresh_token, expires_in=1800, user=user)


@router.post("/auth/login", response_model=AuthResponse, responses=auth_login_error_responses)
def login(payload: LoginRequest) -> AuthResponse:
    user, access_token, refresh_token = workspace_service.login_user(payload.account, payload.password)
    return AuthResponse(access_token=access_token, refresh_token=refresh_token, expires_in=1800, user=user)


@router.post("/auth/refresh", response_model=AuthResponse)
def refresh(payload: RefreshTokenRequest) -> AuthResponse:
    user, access_token, refresh_token = workspace_service.refresh_session(payload.refresh_token)
    return AuthResponse(access_token=access_token, refresh_token=refresh_token, expires_in=1800, user=user)


@router.get("/users/me", response_model=CurrentUserResponse)
def me(user: Annotated[UserPublic, Depends(current_user)]) -> CurrentUserResponse:
    return CurrentUserResponse(user=user)


@router.patch("/users/me", response_model=CurrentUserResponse)
def update_me(payload: UserUpdate, user: Annotated[UserPublic, Depends(current_user)]) -> CurrentUserResponse:
    return CurrentUserResponse(user=workspace_service.update_user_profile(user.id, payload))
