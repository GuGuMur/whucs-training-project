from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile, status

from app.domain.schemas import (
    AgentTaskRequest,
    AgentTaskResponse,
    AuthResponse,
    AuditLogResponse,
    CurrentUserResponse,
    FileItem,
    FileListResponse,
    FolderTreeResponse,
    LoginRequest,
    QARequest,
    QAResponse,
    RefreshTokenRequest,
    TeamListResponse,
    ToolListResponse,
    UserCreate,
    UserPublic,
    UserUpdate,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowListResponse,
    WorkspaceSnapshot,
)
from app.services.workspace import workspace_service


api_router = APIRouter(prefix="/api/v1")


def current_user(authorization: Annotated[str | None, Header()] = None) -> UserPublic:
    return workspace_service.require_user(authorization)


@api_router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate) -> AuthResponse:
    user, access_token, refresh_token = workspace_service.register_user(payload)
    return AuthResponse(access_token=access_token, refresh_token=refresh_token, expires_in=1800, user=user)


@api_router.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    user, access_token, refresh_token = workspace_service.login_user(payload.account, payload.password)
    return AuthResponse(access_token=access_token, refresh_token=refresh_token, expires_in=1800, user=user)


@api_router.post("/auth/refresh", response_model=AuthResponse)
def refresh(payload: RefreshTokenRequest) -> AuthResponse:
    user, access_token, refresh_token = workspace_service.refresh_session(payload.refresh_token)
    return AuthResponse(access_token=access_token, refresh_token=refresh_token, expires_in=1800, user=user)


@api_router.get("/users/me", response_model=CurrentUserResponse)
def me(user: Annotated[UserPublic, Depends(current_user)]) -> CurrentUserResponse:
    return CurrentUserResponse(user=user)


@api_router.patch("/users/me", response_model=CurrentUserResponse)
def update_me(payload: UserUpdate, user: Annotated[UserPublic, Depends(current_user)]) -> CurrentUserResponse:
    return CurrentUserResponse(user=workspace_service.update_user_profile(user.id, payload))


@api_router.get("/folders/tree", response_model=FolderTreeResponse)
def folders(_: Annotated[UserPublic, Depends(current_user)]) -> FolderTreeResponse:
    return FolderTreeResponse(items=workspace_service.folder_tree())


@api_router.get("/files", response_model=FileListResponse)
def files(
    _: Annotated[UserPublic, Depends(current_user)],
    query: str | None = None,
    tag: str | None = None,
    file_type: str | None = None,
) -> FileListResponse:
    items = workspace_service.list_files(query=query, tag=tag, file_type=file_type)
    return FileListResponse(items=items, total=len(items))


@api_router.post("/files/upload", response_model=FileItem, status_code=status.HTTP_201_CREATED)
async def upload_file(
    user: Annotated[UserPublic, Depends(current_user)],
    file: Annotated[UploadFile, File()],
    folder_id: Annotated[str, Form()],
    tags: Annotated[str | None, Form()] = None,
) -> FileItem:
    return await workspace_service.upload_file(file, folder_id, tags, user)


@api_router.post("/qa/query", response_model=QAResponse)
def qa_query(payload: QARequest, user: Annotated[UserPublic, Depends(current_user)]) -> QAResponse:
    return workspace_service.answer_question(payload, user)


@api_router.get("/tools", response_model=ToolListResponse)
def tools(_: Annotated[UserPublic, Depends(current_user)]) -> ToolListResponse:
    return ToolListResponse(items=workspace_service.list_tools())


@api_router.post("/agents/tasks", response_model=AgentTaskResponse, status_code=status.HTTP_201_CREATED)
def create_agent_task(
    payload: AgentTaskRequest,
    user: Annotated[UserPublic, Depends(current_user)],
) -> AgentTaskResponse:
    return workspace_service.create_agent_task(payload, user)


@api_router.get("/workflows", response_model=WorkflowListResponse)
def workflows(_: Annotated[UserPublic, Depends(current_user)]) -> WorkflowListResponse:
    return WorkflowListResponse(items=workspace_service.list_workflows())


@api_router.post(
    "/workflows/{workflow_id}/executions",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
def execute_workflow(
    workflow_id: str,
    payload: WorkflowExecutionRequest,
    user: Annotated[UserPublic, Depends(current_user)],
) -> WorkflowExecutionResponse:
    return workspace_service.execute_workflow(workflow_id, payload, user)


@api_router.get("/teams", response_model=TeamListResponse)
def teams(_: Annotated[UserPublic, Depends(current_user)]) -> TeamListResponse:
    return TeamListResponse(items=workspace_service.list_teams())


@api_router.get("/audit-logs", response_model=AuditLogResponse)
def audit_logs(_: Annotated[UserPublic, Depends(current_user)]) -> AuditLogResponse:
    return AuditLogResponse(items=workspace_service.list_audit_logs())


@api_router.get("/workspace/snapshot", response_model=WorkspaceSnapshot)
def workspace_snapshot(_: Annotated[UserPublic, Depends(current_user)]) -> WorkspaceSnapshot:
    return workspace_service.snapshot()
