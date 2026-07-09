from __future__ import annotations

<<<<<<< HEAD
from urllib.parse import quote
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, Response, UploadFile, status
=======
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile, status
>>>>>>> permission-backend

from app.domain.schemas import (
    AgentTaskRequest,
    AgentTaskResponse,
    AuthResponse,
    AuditLogResponse,
    CurrentUserResponse,
<<<<<<< HEAD
    ErrorResponse,
    FileCopyRequest,
    FileItem,
    FileListResponse,
    FileUpdate,
    FileVersionListResponse,
    FolderCreate,
    FolderItem,
    FolderTreeResponse,
    FolderUpdate,
=======
    FileItem,
    FileListResponse,
    FolderTreeResponse,
>>>>>>> permission-backend
    LoginRequest,
    QARequest,
    QAResponse,
    RefreshTokenRequest,
<<<<<<< HEAD
    TeamCreate,
    TeamDetail,
    TeamInviteCreate,
    TeamInvitePublic,
    TeamListResponse,
    TeamMemberJoin,
    TeamMemberPublic,
    TeamMemberUpdate,
=======
    TeamListResponse,
>>>>>>> permission-backend
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
<<<<<<< HEAD
auth_login_error_responses = {
    401: {"model": ErrorResponse, "description": "Invalid credentials"},
    423: {"model": ErrorResponse, "description": "Account temporarily locked"},
}
=======
>>>>>>> permission-backend


def current_user(authorization: Annotated[str | None, Header()] = None) -> UserPublic:
    return workspace_service.require_user(authorization)


@api_router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate) -> AuthResponse:
    user, access_token, refresh_token = workspace_service.register_user(payload)
    return AuthResponse(access_token=access_token, refresh_token=refresh_token, expires_in=1800, user=user)


<<<<<<< HEAD
@api_router.post("/auth/login", response_model=AuthResponse, responses=auth_login_error_responses)
=======
@api_router.post("/auth/login", response_model=AuthResponse)
>>>>>>> permission-backend
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
<<<<<<< HEAD
def folders(user: Annotated[UserPublic, Depends(current_user)]) -> FolderTreeResponse:
    return FolderTreeResponse(items=workspace_service.folder_tree(user))


@api_router.post("/folders", response_model=FolderItem, status_code=status.HTTP_201_CREATED)
def create_folder(payload: FolderCreate, user: Annotated[UserPublic, Depends(current_user)]) -> FolderItem:
    return workspace_service.create_folder(payload, user)


@api_router.patch("/folders/{folder_id}", response_model=FolderItem)
def update_folder(
    folder_id: str,
    payload: FolderUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FolderItem:
    return workspace_service.update_folder(folder_id, payload, user)


@api_router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(folder_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> Response:
    workspace_service.delete_folder(folder_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
=======
def folders(_: Annotated[UserPublic, Depends(current_user)]) -> FolderTreeResponse:
    return FolderTreeResponse(items=workspace_service.folder_tree())
>>>>>>> permission-backend


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


<<<<<<< HEAD
@api_router.patch("/files/{file_id}", response_model=FileItem)
def update_file(
    file_id: str,
    payload: FileUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FileItem:
    return workspace_service.update_file(file_id, payload, user)


@api_router.post("/files/{file_id}/copy", response_model=FileItem, status_code=status.HTTP_201_CREATED)
def copy_file(
    file_id: str,
    payload: FileCopyRequest,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FileItem:
    return workspace_service.copy_file(file_id, payload, user)


@api_router.get("/files/{file_id}/download")
def download_file(file_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> Response:
    file_item, content = workspace_service.download_file(file_id, user)
    encoded_name = quote(file_item.name, safe="")
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"},
    )


@api_router.get("/files/{file_id}/versions", response_model=FileVersionListResponse)
def file_versions(file_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> FileVersionListResponse:
    return FileVersionListResponse(items=workspace_service.list_file_versions(file_id, user))


@api_router.post("/files/{file_id}/versions/{version_id}/restore", response_model=FileItem)
def restore_file_version(
    file_id: str,
    version_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FileItem:
    return workspace_service.restore_file_version(file_id, version_id, user)


@api_router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> Response:
    workspace_service.delete_file(file_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


=======
>>>>>>> permission-backend
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


<<<<<<< HEAD
@api_router.post("/teams", response_model=TeamDetail, status_code=status.HTTP_201_CREATED)
def create_team(payload: TeamCreate, user: Annotated[UserPublic, Depends(current_user)]) -> TeamDetail:
    return workspace_service.create_team(payload, user)


@api_router.get("/teams", response_model=TeamListResponse)
def teams(user: Annotated[UserPublic, Depends(current_user)]) -> TeamListResponse:
    return TeamListResponse(items=workspace_service.list_teams(user))


@api_router.get("/teams/{team_id}", response_model=TeamDetail)
def team_detail(team_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> TeamDetail:
    return workspace_service.get_team_detail(team_id, user)


@api_router.post("/teams/{team_id}/invites", response_model=TeamInvitePublic, status_code=status.HTTP_201_CREATED)
def create_team_invite(
    team_id: str,
    payload: TeamInviteCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> TeamInvitePublic:
    return workspace_service.create_team_invite(team_id, payload, user)


@api_router.post("/teams/{team_id}/members", response_model=TeamMemberPublic, status_code=status.HTTP_201_CREATED)
def join_team(
    team_id: str,
    payload: TeamMemberJoin,
    user: Annotated[UserPublic, Depends(current_user)],
) -> TeamMemberPublic:
    return workspace_service.join_team(team_id, payload, user)


@api_router.patch("/teams/{team_id}/members/{member_id}", response_model=TeamMemberPublic)
def update_team_member(
    team_id: str,
    member_id: str,
    payload: TeamMemberUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> TeamMemberPublic:
    return workspace_service.update_team_member(team_id, member_id, payload, user)


@api_router.delete("/teams/{team_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    team_id: str,
    member_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> Response:
    workspace_service.remove_team_member(team_id, member_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
=======
@api_router.get("/teams", response_model=TeamListResponse)
def teams(_: Annotated[UserPublic, Depends(current_user)]) -> TeamListResponse:
    return TeamListResponse(items=workspace_service.list_teams())
>>>>>>> permission-backend


@api_router.get("/audit-logs", response_model=AuditLogResponse)
def audit_logs(_: Annotated[UserPublic, Depends(current_user)]) -> AuditLogResponse:
    return AuditLogResponse(items=workspace_service.list_audit_logs())


@api_router.get("/workspace/snapshot", response_model=WorkspaceSnapshot)
<<<<<<< HEAD
def workspace_snapshot(user: Annotated[UserPublic, Depends(current_user)]) -> WorkspaceSnapshot:
    return workspace_service.snapshot(user)
=======
def workspace_snapshot(_: Annotated[UserPublic, Depends(current_user)]) -> WorkspaceSnapshot:
    return workspace_service.snapshot()
>>>>>>> permission-backend
