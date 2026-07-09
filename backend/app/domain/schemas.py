from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    account: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    email: str | None = Field(
        default=None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserPublic(BaseModel):
    id: int
    username: str
    email: str
    display_name: str
    roles: list[str]


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserPublic


class CurrentUserResponse(BaseModel):
    user: UserPublic


class FolderItem(BaseModel):
    id: str
    name: str
    parent_id: str | None = None
    scope: Literal["personal", "team"]
    permission: str
    team_id: str | None = None
    children: list["FolderItem"] = Field(default_factory=list)


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    parent_id: str | None = None
    scope: Literal["personal", "team"] = "personal"


class FolderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    parent_id: str | None = None


class FolderTreeResponse(BaseModel):
    items: list[FolderItem]


class FileItem(BaseModel):
    id: str
    name: str
    folder_id: str
    type: str
    size: int
    sha256: str
    parse_status: Literal["queued", "parsing", "indexed", "failed"]
    tags: list[str]
    updated_at: datetime
    permission_scope: str
    knowledge_base_ids: list[str]


class FileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    folder_id: str | None = None
    tags: list[str] | None = None


class FileCopyRequest(BaseModel):
    target_folder_id: str = Field(min_length=1)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    tags: list[str] | None = None


class FileVersionItem(BaseModel):
    id: str
    file_id: str
    version_no: int
    name: str
    size: int
    sha256: str
    created_at: datetime
    created_by: str
    is_current: bool


class FileVersionListResponse(BaseModel):
    items: list[FileVersionItem]


class FileListResponse(BaseModel):
    items: list[FileItem]
    total: int


PermissionSubjectType = Literal["user", "team", "role"]
PermissionResourceType = Literal["file",
                                 "folder", "knowledge_base", "tool", "workflow"]
PermissionAction = Literal["read", "write", "delete", "manage", "execute"]
PermissionEffect = Literal["allow", "deny"]


class PermissionRuleCreate(BaseModel):
    subject_type: PermissionSubjectType
    subject_id: str = Field(min_length=1)
    resource_type: PermissionResourceType
    resource_id: str = Field(min_length=1)
    action: PermissionAction
    effect: PermissionEffect
    inherit: bool = False


class PermissionRulePublic(BaseModel):
    id: str
    subject_type: PermissionSubjectType
    subject_id: str
    subject_label: str
    resource_type: PermissionResourceType
    resource_id: str
    resource_label: str
    action: PermissionAction
    effect: PermissionEffect
    inherit: bool
    created_at: datetime
    created_by: str


class PermissionRuleListResponse(BaseModel):
    items: list[PermissionRulePublic]


class Citation(BaseModel):
    file_id: str
    document_id: str
    chunk_id: str
    title: str
    page_no: int
    paragraph_no: int
    snippet: str


class QARequest(BaseModel):
    kb_id: str
    conversation_id: str | None = None
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    stream: bool = False


class QAResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    citations: list[Citation]


KnowledgeBaseStatus = Literal["active", "archived"]
KnowledgeIndexStatus = Literal["queued", "indexing", "indexed", "failed"]


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    status: KnowledgeBaseStatus | None = None


class KnowledgeBasePublic(BaseModel):
    id: str
    name: str
    description: str
    status: KnowledgeBaseStatus
    document_count: int
    chunk_count: int
    updated_at: datetime


class KnowledgeBaseListResponse(BaseModel):
    items: list[KnowledgeBasePublic]


class KnowledgeDocumentCreate(BaseModel):
    file_id: str = Field(min_length=1)


class KnowledgeDocumentPublic(BaseModel):
    id: str
    kb_id: str
    file_id: str
    file_name: str
    index_status: KnowledgeIndexStatus
    chunk_count: int
    updated_at: datetime


class KnowledgeDocumentListResponse(BaseModel):
    items: list[KnowledgeDocumentPublic]


class ToolDefinition(BaseModel):
    id: str
    name: str
    version: str
    category: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    enabled: bool = True


class ToolListResponse(BaseModel):
    items: list[ToolDefinition]


class AgentTaskRequest(BaseModel):
    task: str = Field(min_length=1)
    kb_id: str | None = None
    context_file_ids: list[str] = Field(default_factory=list)


class AgentStep(BaseModel):
    type: Literal["thought", "action", "observation", "answer"]
    title: str
    content: str
    tool_name: str | None = None
    status: Literal["pending", "running", "success", "failed"] = "success"
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentTaskResponse(BaseModel):
    id: str
    task: str
    status: Literal["queued", "running", "completed", "failed"]
    steps: list[AgentStep]
    final_answer: str


WorkflowNodeType = Literal["trigger", "tool",
                           "condition", "loop", "aggregate", "output"]


class WorkflowNodeDefinition(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    type: WorkflowNodeType
    tool_name: str | None = Field(default=None, max_length=80)
    parameters: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, float] = Field(default_factory=dict)


class WorkflowEdgeDefinition(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    source: str = Field(min_length=1, max_length=64)
    target: str = Field(min_length=1, max_length=64)
    source_handle: str | None = None
    target_handle: str | None = None


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    trigger: str = Field(default="manual", min_length=1, max_length=80)
    nodes: list[WorkflowNodeDefinition] = Field(default_factory=list)
    edges: list[WorkflowEdgeDefinition] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    trigger: str | None = Field(default=None, min_length=1, max_length=80)
    nodes: list[WorkflowNodeDefinition] | None = None
    edges: list[WorkflowEdgeDefinition] | None = None


class WorkflowValidationIssue(BaseModel):
    code: str
    message: str
    node_id: str | None = None
    edge_id: str | None = None


class WorkflowValidationResponse(BaseModel):
    valid: bool
    issues: list[WorkflowValidationIssue]
    node_count: int
    edge_count: int


class WorkflowDefinition(BaseModel):
    id: str
    name: str
    description: str
    trigger: str
    version: str
    node_count: int
    status: Literal["draft", "published"]
    nodes: list[WorkflowNodeDefinition] = Field(default_factory=list)
    edges: list[WorkflowEdgeDefinition] = Field(default_factory=list)


class WorkflowListResponse(BaseModel):
    items: list[WorkflowDefinition]


class WorkflowExecutionRequest(BaseModel):
    file_id: str
    target_kb_id: str | None = None


class WorkflowNodeExecution(BaseModel):
    node_id: str
    name: str
    tool_name: str
    status: Literal["pending", "running", "success", "failed"]
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    status: Literal["queued", "running", "completed", "failed"]
    node_executions: list[WorkflowNodeExecution]
    output: dict[str, Any]


class TeamSummary(BaseModel):
    id: str
    name: str
    description: str = ""
    role: str
    member_count: int
    unread_count: int
    root_folder_id: str | None = None


class TeamListResponse(BaseModel):
    items: list[TeamSummary]


TeamRole = Literal["owner", "admin", "member", "guest"]
TeamMemberStatus = Literal["active", "invited", "removed"]
TeamInviteStatus = Literal["pending", "accepted", "revoked", "expired"]


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)


class TeamInviteCreate(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role: TeamRole = "member"


class TeamMemberJoin(BaseModel):
    invite_token: str = Field(min_length=1)


class TeamMemberUpdate(BaseModel):
    role: TeamRole


class TeamMemberPublic(BaseModel):
    id: str
    team_id: str
    user_id: int
    username: str
    email: str
    display_name: str
    role: TeamRole
    status: TeamMemberStatus
    joined_at: datetime


class TeamInvitePublic(BaseModel):
    id: str
    team_id: str
    email: str
    role: TeamRole
    status: TeamInviteStatus
    token: str
    created_at: datetime
    expires_at: datetime


class TeamDetail(BaseModel):
    id: str
    name: str
    description: str
    role: TeamRole
    member_count: int
    unread_count: int
    root_folder: FolderItem
    members: list[TeamMemberPublic]
    invites: list[TeamInvitePublic]


class AuditLogEntry(BaseModel):
    id: str
    actor: str
    action: str
    resource_type: str
    resource_name: str
    created_at: datetime


class AuditLogResponse(BaseModel):
    items: list[AuditLogEntry]


class DashboardSummary(BaseModel):
    file_count: int
    indexed_count: int
    knowledge_base_count: int
    running_workflows: int
    unread_notifications: int
    tools_enabled: int


class WorkspaceSnapshot(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    summary: DashboardSummary
    files: list[FileItem]
    tools: list[ToolDefinition]
    workflows: list[WorkflowDefinition]
    teams: list[TeamSummary]
    audit_logs: list[AuditLogEntry]
