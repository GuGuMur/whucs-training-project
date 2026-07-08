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
    email: str | None = Field(default=None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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
    children: list["FolderItem"] = Field(default_factory=list)


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


class FileListResponse(BaseModel):
    items: list[FileItem]
    total: int


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


class WorkflowDefinition(BaseModel):
    id: str
    name: str
    description: str
    trigger: str
    version: str
    node_count: int
    status: Literal["draft", "published"]


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
    role: str
    member_count: int
    unread_count: int


class TeamListResponse(BaseModel):
    items: list[TeamSummary]


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
