#这其实就是一个枚举文件

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class SystemRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    TEAM_ADMIN = "team_admin"
    MEMBER = "member"
    GUEST = "guest"


class ResourceType(str, Enum):
    FILE = "file"
    FOLDER = "folder"
    KNOWLEDGE_BASE = "knowledge_base"
    TOOL = "tool"
    WORKFLOW_TEMPLATE = "workflow_template"
    TEAM = "team"


class PermissionLevel(str, Enum):
    NONE = "none"
    READ = "read"
    WRITE = "write"
    MANAGE = "manage"


class KnowledgeVisibility(str, Enum):
    PRIVATE = "private"
    TEAM = "team"
    PUBLIC = "public"


class AuditAction(str, Enum):
    CREATE_ROLE = "create_role"
    ASSIGN_ROLE = "assign_role"
    GRANT_PERMISSION = "grant_permission"
    SET_RESOURCE_PARENT = "set_resource_parent"
    CHECK_PERMISSION = "check_permission"
    GRANT_TOOL = "grant_tool"
    UPDATE_KB_VISIBILITY = "update_kb_visibility"


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    system_role: SystemRole | None = None


class RoleRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    system_role: SystemRole | None = None
    is_builtin: bool = False


class UserRoleAssign(BaseModel):
    user_id: int
    role_id: int
    team_id: int | None = None


class PermissionGrant(BaseModel):
    subject_type: Literal["user", "role"]
    subject_id: int
    resource_type: ResourceType
    resource_id: int
    level: PermissionLevel
    inherit: bool = True


class ResourceParentSet(BaseModel):
    resource_type: ResourceType
    resource_id: int
    parent_type: ResourceType
    parent_id: int


class PermissionCheck(BaseModel):
    user_id: int
    resource_type: ResourceType
    resource_id: int
    required_level: PermissionLevel


class PermissionDecision(BaseModel):
    allowed: bool
    effective_level: PermissionLevel
    reason: str


class ToolPermissionGrant(BaseModel):
    tool_id: int
    subject_type: Literal["user", "role"]
    subject_id: int
    allow_execute: bool = True


class KnowledgeBaseVisibilityUpdate(BaseModel):
    kb_id: int
    owner_id: int
    team_id: int | None = None
    visibility: KnowledgeVisibility


class AuditLogRead(BaseModel):
    id: int
    actor_id: int | None = None
    action: AuditAction | str
    resource_type: str
    resource_id: int | None = None
    detail: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

