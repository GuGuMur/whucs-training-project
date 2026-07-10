from __future__ import annotations

from datetime import datetime
from urllib.parse import quote
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, Response, UploadFile, WebSocket, status
from fastapi.responses import StreamingResponse

from app.domain.schemas import (
    AgentTaskRequest,
    AgentTaskResponse,
    AuthResponse,
    AuditLogResponse,
    CurrentUserResponse,
    ErrorResponse,
    FileCopyRequest,
    FileAnnotationCreate,
    FileAnnotationItem,
    FileAnnotationListResponse,
    FileAnnotationReplyCreate,
    FileAnnotationReplyItem,
    FileItem,
    FileListResponse,
    FileUpdate,
    FileVersionListResponse,
    FolderCreate,
    FolderItem,
    FolderTreeResponse,
    FolderUpdate,
    KnowledgeBaseCreate,
    KnowledgeBaseListResponse,
    KnowledgeBasePublic,
    KnowledgeBaseUpdate,
    KnowledgeDocumentCreate,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentPublic,
    LoginRequest,
    MultipartChunkResponse,
    MultipartUploadInitRequest,
    MultipartUploadSession,
    NotificationItem,
    NotificationListResponse,
    PermissionRuleCreate,
    PermissionRuleListResponse,
    PermissionRulePublic,
    QARequest,
    QAResponse,
    RefreshTokenRequest,
    RecycleBinResponse,
    ShareLinkCreateRequest,
    ShareLinkDownloadRequest,
    ShareLinkPublic,
    TeamCreate,
    TeamDetail,
    TeamInviteCreate,
    TeamInvitePublic,
    TeamListResponse,
    TeamMessageCreate,
    TeamMessageItem,
    TeamMessageListResponse,
    TeamMemberJoin,
    TeamMemberPublic,
    TeamMemberUpdate,
    ToolListResponse,
    UserCreate,
    UserPublic,
    UserUpdate,
    WorkflowCreate,
    WorkflowDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowListResponse,
    WorkflowUpdate,
    WorkflowValidationResponse,
    WorkspaceSnapshot,
)
from app.services.workspace import workspace_service


api_router = APIRouter(prefix="/api/v1")
auth_login_error_responses = {
    401: {"model": ErrorResponse, "description": "Invalid credentials"},
    423: {"model": ErrorResponse, "description": "Account temporarily locked"},
}


def current_user(authorization: Annotated[str | None, Header()] = None) -> UserPublic:
    return workspace_service.require_user(authorization)


@api_router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate) -> AuthResponse:
    user, access_token, refresh_token = workspace_service.register_user(payload)
    return AuthResponse(access_token=access_token, refresh_token=refresh_token, expires_in=1800, user=user)


@api_router.post("/auth/login", response_model=AuthResponse, responses=auth_login_error_responses)
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


@api_router.get("/files", response_model=FileListResponse)
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


@api_router.post("/files/upload", response_model=FileItem, status_code=status.HTTP_201_CREATED)
async def upload_file(
    user: Annotated[UserPublic, Depends(current_user)],
    file: Annotated[UploadFile, File()],
    folder_id: Annotated[str, Form()],
    tags: Annotated[str | None, Form()] = None,
) -> FileItem:
    return await workspace_service.upload_file(file, folder_id, tags, user)


@api_router.post(
    "/files/multipart-uploads",
    response_model=MultipartUploadSession,
    status_code=status.HTTP_201_CREATED,
)
def init_multipart_upload(
    payload: MultipartUploadInitRequest,
    user: Annotated[UserPublic, Depends(current_user)],
) -> MultipartUploadSession:
    return workspace_service.init_multipart_upload(payload, user)


@api_router.get("/files/multipart-uploads/{session_id}", response_model=MultipartUploadSession)
def multipart_upload_status(
    session_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> MultipartUploadSession:
    return workspace_service.get_multipart_upload(session_id, user)


@api_router.put("/files/multipart-uploads/{session_id}/chunks/{chunk_index}", response_model=MultipartChunkResponse)
async def upload_multipart_chunk(
    session_id: str,
    chunk_index: int,
    user: Annotated[UserPublic, Depends(current_user)],
    chunk: Annotated[UploadFile, File()],
    sha256: Annotated[str, Form()],
) -> MultipartChunkResponse:
    return await workspace_service.upload_multipart_chunk(session_id, chunk_index, chunk, sha256, user)


@api_router.post(
    "/files/multipart-uploads/{session_id}/complete",
    response_model=FileItem,
    status_code=status.HTTP_201_CREATED,
)
def complete_multipart_upload(
    session_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FileItem:
    return workspace_service.complete_multipart_upload(session_id, user)


@api_router.get("/files/recycle-bin", response_model=RecycleBinResponse)
def recycle_bin(user: Annotated[UserPublic, Depends(current_user)]) -> RecycleBinResponse:
    items = workspace_service.list_deleted_files(user)
    return RecycleBinResponse(items=items, total=len(items))


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


@api_router.post("/files/{file_id}/share-links", response_model=ShareLinkPublic, status_code=status.HTTP_201_CREATED)
def create_file_share_link(
    file_id: str,
    payload: ShareLinkCreateRequest,
    user: Annotated[UserPublic, Depends(current_user)],
) -> ShareLinkPublic:
    return workspace_service.create_share_link(file_id, payload, user)


@api_router.get("/files/{file_id}/annotations", response_model=FileAnnotationListResponse)
def file_annotations(
    file_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> FileAnnotationListResponse:
    items = workspace_service.list_file_annotations(file_id, user)
    return FileAnnotationListResponse(items=items, total=len(items))


@api_router.post(
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


@api_router.post(
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


@api_router.delete("/files/{file_id}/annotations/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file_annotation(
    file_id: str,
    annotation_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> Response:
    workspace_service.delete_file_annotation(file_id, annotation_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api_router.get("/files/{file_id}/download")
def download_file(file_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> Response:
    file_item, content = workspace_service.download_file(file_id, user)
    encoded_name = quote(file_item.name, safe="")
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"},
    )


@api_router.post("/share-links/{token}/download")
def download_shared_file(token: str, payload: ShareLinkDownloadRequest | None = None) -> Response:
    file_item, content = workspace_service.download_shared_file(token, payload.password if payload else None)
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


@api_router.post("/files/{file_id}/restore", response_model=FileItem)
def restore_deleted_file(file_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> FileItem:
    return workspace_service.restore_deleted_file(file_id, user)


@api_router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> Response:
    workspace_service.delete_file(file_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api_router.get("/knowledge-bases", response_model=KnowledgeBaseListResponse)
def knowledge_bases(user: Annotated[UserPublic, Depends(current_user)]) -> KnowledgeBaseListResponse:
    return KnowledgeBaseListResponse(items=workspace_service.list_knowledge_bases(user))


@api_router.post("/knowledge-bases", response_model=KnowledgeBasePublic, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> KnowledgeBasePublic:
    return workspace_service.create_knowledge_base(payload, user)


@api_router.patch("/knowledge-bases/{kb_id}", response_model=KnowledgeBasePublic)
def update_knowledge_base(
    kb_id: str,
    payload: KnowledgeBaseUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> KnowledgeBasePublic:
    return workspace_service.update_knowledge_base(kb_id, payload, user)


@api_router.get("/knowledge-bases/{kb_id}/documents", response_model=KnowledgeDocumentListResponse)
def knowledge_documents(
    kb_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> KnowledgeDocumentListResponse:
    return KnowledgeDocumentListResponse(items=workspace_service.list_knowledge_documents(kb_id, user))


@api_router.post(
    "/knowledge-bases/{kb_id}/documents",
    response_model=KnowledgeDocumentPublic,
    status_code=status.HTTP_201_CREATED,
)
def add_knowledge_document(
    kb_id: str,
    payload: KnowledgeDocumentCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> KnowledgeDocumentPublic:
    return workspace_service.add_knowledge_document(kb_id, payload, user)


@api_router.post("/qa/query", response_model=QAResponse)
def qa_query(payload: QARequest, user: Annotated[UserPublic, Depends(current_user)]) -> QAResponse:
    return workspace_service.answer_question(payload, user)


@api_router.post("/qa/query/stream")
async def qa_query_stream(payload: QARequest, user: Annotated[UserPublic, Depends(current_user)]):
    """Streaming QA endpoint using Server-Sent Events."""
    from app.services.llm import generate_rag_answer_stream

    citations = workspace_service._retrieve_knowledge_citations(
        payload.kb_id, payload.question, payload.top_k, user,
    )
    snippets = [c.snippet for c in citations[:5]]
    kb_name = workspace_service._knowledge_bases.get(payload.kb_id)
    kb_label = kb_name.name if kb_name else payload.kb_id

    async def event_stream():
        for chunk in generate_rag_answer_stream(payload.question, snippets, kb_label):
            yield f"data: {chunk}\n\n"
        # Send citations as final event
        import json

        citation_data = json.dumps(
            [{"title": c.title, "snippet": c.snippet, "page_no": c.page_no} for c in citations],
            ensure_ascii=False,
        )
        yield f"event: citations\ndata: {citation_data}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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


@api_router.post("/workflows", response_model=WorkflowDefinition, status_code=status.HTTP_201_CREATED)
def create_workflow(
    payload: WorkflowCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> WorkflowDefinition:
    return workspace_service.create_workflow(payload, user)


@api_router.patch("/workflows/{workflow_id}", response_model=WorkflowDefinition)
def update_workflow(
    workflow_id: str,
    payload: WorkflowUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> WorkflowDefinition:
    return workspace_service.update_workflow(workflow_id, payload, user)


@api_router.post("/workflows/{workflow_id}/validate", response_model=WorkflowValidationResponse)
def validate_workflow(
    workflow_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> WorkflowValidationResponse:
    return workspace_service.validate_workflow(workflow_id, user)


@api_router.post("/workflows/{workflow_id}/publish", response_model=WorkflowDefinition)
def publish_workflow(
    workflow_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> WorkflowDefinition:
    return workspace_service.publish_workflow(workflow_id, user)


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


@api_router.post("/teams", response_model=TeamDetail, status_code=status.HTTP_201_CREATED)
def create_team(payload: TeamCreate, user: Annotated[UserPublic, Depends(current_user)]) -> TeamDetail:
    return workspace_service.create_team(payload, user)


@api_router.get("/teams", response_model=TeamListResponse)
def teams(user: Annotated[UserPublic, Depends(current_user)]) -> TeamListResponse:
    return TeamListResponse(items=workspace_service.list_teams(user))


@api_router.get("/teams/{team_id}", response_model=TeamDetail)
def team_detail(team_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> TeamDetail:
    return workspace_service.get_team_detail(team_id, user)


@api_router.get("/teams/{team_id}/messages", response_model=TeamMessageListResponse)
def team_messages(team_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> TeamMessageListResponse:
    items = workspace_service.list_team_messages(team_id, user)
    return TeamMessageListResponse(items=items, total=len(items))


@api_router.post("/teams/{team_id}/messages", response_model=TeamMessageItem, status_code=status.HTTP_201_CREATED)
def create_team_message(
    team_id: str,
    payload: TeamMessageCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> TeamMessageItem:
    return workspace_service.create_team_message(team_id, payload, user)


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


@api_router.get("/permissions/rules", response_model=PermissionRuleListResponse)
def permission_rules(user: Annotated[UserPublic, Depends(current_user)]) -> PermissionRuleListResponse:
    return PermissionRuleListResponse(items=workspace_service.list_permission_rules(user))


@api_router.post("/permissions/rules", response_model=PermissionRulePublic, status_code=status.HTTP_201_CREATED)
def create_permission_rule(
    payload: PermissionRuleCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> PermissionRulePublic:
    return workspace_service.create_permission_rule(payload, user)


@api_router.delete("/permissions/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission_rule(rule_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> Response:
    workspace_service.delete_permission_rule(rule_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api_router.get("/notifications", response_model=NotificationListResponse)
def notifications(user: Annotated[UserPublic, Depends(current_user)]) -> NotificationListResponse:
    items = workspace_service.list_notifications(user)
    unread_count = sum(1 for item in items if not item.is_read)
    return NotificationListResponse(items=items, total=len(items), unread_count=unread_count)


@api_router.patch("/notifications/{notification_id}/read", response_model=NotificationItem)
def mark_notification_read(
    notification_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> NotificationItem:
    return workspace_service.mark_notification_read(notification_id, user)


@api_router.get("/audit-logs", response_model=AuditLogResponse)
def audit_logs(_: Annotated[UserPublic, Depends(current_user)]) -> AuditLogResponse:
    return AuditLogResponse(items=workspace_service.list_audit_logs())


@api_router.get("/workspace/snapshot", response_model=WorkspaceSnapshot)
def workspace_snapshot(user: Annotated[UserPublic, Depends(current_user)]) -> WorkspaceSnapshot:
    return workspace_service.snapshot(user)


# ── WebSocket ──────────────────────────────────────────────────────────

@api_router.websocket("/ws")
async def ws_connect(ws: WebSocket, token: str = ""):
    """Authenticated WebSocket for real-time push.

    Query params: token (JWT), channels (comma-separated: workflow,chat,activity)
    """
    from urllib.parse import parse_qs

    from app.services.websocket_manager import ws_manager

    # Parse query string from WebSocket scope
    qs = parse_qs(ws.scope.get("query_string", b"").decode())
    token = qs.get("token", [""])[0]
    channels_str = qs.get("channels", ["workflow"])[0]
    channels = [c.strip() for c in channels_str.split(",") if c.strip()]

    # Authenticate
    try:
        user = workspace_service.require_user(f"Bearer {token}")
    except Exception:
        await ws.close(code=4001)
        return

    await ws_manager.connect(ws, channels)
    try:
        while True:
            await ws.receive_text()
    except Exception:
        pass
    finally:
        await ws_manager.disconnect(ws)
