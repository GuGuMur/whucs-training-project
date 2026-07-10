from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)


NotificationType = Literal["invite", "mention", "annotation", "workflow", "system"]


class NotificationItem(BaseModel):
    id: str
    user_id: int
    type: NotificationType
    title: str
    content: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationItem]
    total: int
    unread_count: int


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
    files: list["FileItem"]
    tools: list["ToolDefinition"]
    workflows: list["WorkflowDefinition"]
    teams: list["TeamSummary"]
    audit_logs: list[AuditLogEntry]

# Rebuild models with forward references
from app.domain.file import FileItem
from app.domain.workflow import ToolDefinition, WorkflowDefinition
from app.domain.team import TeamSummary
WorkspaceSnapshot.model_rebuild()
