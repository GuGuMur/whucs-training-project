from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.security.schemas import (
    AuditAction,
    AuditLogRead,
    KnowledgeBaseVisibilityUpdate,
    KnowledgeVisibility,
    PermissionDecision,
    PermissionGrant,
    PermissionLevel,
    ResourceParentSet,
    ResourceType,
    RoleCreate,
    RoleRead,
    SystemRole,
    ToolPermissionGrant,
    UserRoleAssign,
)


LEVEL_RANK: dict[PermissionLevel, int] = {
    PermissionLevel.NONE: 0,
    PermissionLevel.READ: 1,
    PermissionLevel.WRITE: 2,
    PermissionLevel.MANAGE: 3,
}


@dataclass
class PermissionRule:
    subject_type: str
    subject_id: int
    resource_type: ResourceType
    resource_id: int
    level: PermissionLevel
    inherit: bool = True


@dataclass
class InMemoryPermissionStore:
    roles: dict[int, RoleRead] = field(default_factory=dict)
    user_roles: list[UserRoleAssign] = field(default_factory=list)
    permission_rules: list[PermissionRule] = field(default_factory=list)
    parent_resources: dict[tuple[ResourceType, int], tuple[ResourceType, int]] = field(default_factory=dict)
    tool_permissions: list[ToolPermissionGrant] = field(default_factory=list)
    knowledge_bases: dict[int, KnowledgeBaseVisibilityUpdate] = field(default_factory=dict)
    audit_logs: list[AuditLogRead] = field(default_factory=list)
    next_role_id: int = 1
    next_audit_id: int = 1


class PermissionService:
    def __init__(self) -> None:
        self.store = InMemoryPermissionStore()
        self._seed_builtin_roles()

    #创建用户身份
    def _seed_builtin_roles(self) -> None:
        for role in SystemRole:
            self.create_role(
                RoleCreate(
                    name=role.value,
                    description=f"Built-in role: {role.value}",
                    system_role=role,
                ),
                actor_id=None,
                is_builtin=True,
            )

    def create_role(
        self,
        payload: RoleCreate,
        actor_id: int | None,
        is_builtin: bool = False,
    ) -> RoleRead:
        role = RoleRead(
            id=self.store.next_role_id,
            name=payload.name,
            description=payload.description,
            system_role=payload.system_role,
            is_builtin=is_builtin,
        )
        self.store.roles[role.id] = role
        self.store.next_role_id += 1
        self.record_audit(
            actor_id=actor_id,
            action=AuditAction.CREATE_ROLE,
            resource_type="role",
            resource_id=role.id,
            detail={"name": role.name, "system_role": role.system_role},
        )
        return role

    def list_roles(self) -> list[RoleRead]:
        return list(self.store.roles.values())

    def assign_role(self, payload: UserRoleAssign, actor_id: int | None) -> UserRoleAssign:
        if payload.role_id not in self.store.roles:
            raise ValueError("role does not exist")
        self.store.user_roles.append(payload)
        self.record_audit(
            actor_id=actor_id,
            action=AuditAction.ASSIGN_ROLE,
            resource_type="user",
            resource_id=payload.user_id,
            detail=payload.model_dump(),
        )
        return payload

    def grant_permission(self, payload: PermissionGrant, actor_id: int | None) -> PermissionGrant:
        self.store.permission_rules.append(PermissionRule(**payload.model_dump()))
        self.record_audit(
            actor_id=actor_id,
            action=AuditAction.GRANT_PERMISSION,
            resource_type=payload.resource_type.value,
            resource_id=payload.resource_id,
            detail=payload.model_dump(mode="json"),
        )
        return payload
    
    #下面是资源继承的问题

    def set_resource_parent(self, payload: ResourceParentSet, actor_id: int | None) -> ResourceParentSet:
        self.store.parent_resources[(payload.resource_type, payload.resource_id)] = (
            payload.parent_type,
            payload.parent_id,
        )
        self.record_audit(
            actor_id=actor_id,
            action=AuditAction.SET_RESOURCE_PARENT,
            resource_type=payload.resource_type.value,
            resource_id=payload.resource_id,
            detail=payload.model_dump(mode="json"),
        )
        return payload

    def check_permission(
        self,
        user_id: int,
        resource_type: ResourceType,
        resource_id: int,
        required_level: PermissionLevel,
        actor_id: int | None = None,
    ) -> PermissionDecision:
        user_role_ids = {
            assigned.role_id
            for assigned in self.store.user_roles
            if assigned.user_id == user_id
        }
        roles = [self.store.roles[role_id] for role_id in user_role_ids if role_id in self.store.roles]

        if any(role.system_role == SystemRole.SUPER_ADMIN for role in roles):
            decision = PermissionDecision(
                allowed=True,
                effective_level=PermissionLevel.MANAGE,
                reason="super admin role grants all permissions",
            )
            self._audit_permission_check(actor_id, user_id, resource_type, resource_id, required_level, decision)
            return decision

        effective = self._resolve_resource_level(user_id, user_role_ids, resource_type, resource_id)
        allowed = LEVEL_RANK[effective] >= LEVEL_RANK[required_level]
        decision = PermissionDecision(
            allowed=allowed,
            effective_level=effective,
            reason="matched direct or inherited rule" if effective != PermissionLevel.NONE else "no matching rule",
        )
        self._audit_permission_check(actor_id, user_id, resource_type, resource_id, required_level, decision)
        return decision

    def grant_tool_permission(
        self,
        payload: ToolPermissionGrant,
        actor_id: int | None,
    ) -> ToolPermissionGrant:
        self.store.tool_permissions.append(payload)
        self.record_audit(
            actor_id=actor_id,
            action=AuditAction.GRANT_TOOL,
            resource_type=ResourceType.TOOL.value,
            resource_id=payload.tool_id,
            detail=payload.model_dump(),
        )
        return payload

    def can_execute_tool(self, user_id: int, tool_id: int) -> PermissionDecision:
        role_ids = {item.role_id for item in self.store.user_roles if item.user_id == user_id}
        for grant in reversed(self.store.tool_permissions):
            if grant.tool_id != tool_id:
                continue
            user_match = grant.subject_type == "user" and grant.subject_id == user_id
            role_match = grant.subject_type == "role" and grant.subject_id in role_ids
            if user_match or role_match:
                return PermissionDecision(
                    allowed=grant.allow_execute,
                    effective_level=PermissionLevel.MANAGE if grant.allow_execute else PermissionLevel.NONE,
                    reason="matched tool execution permission",
                )
        return PermissionDecision(
            allowed=False,
            effective_level=PermissionLevel.NONE,
            reason="no tool execution permission",
        )

    def update_kb_visibility(
        self,
        payload: KnowledgeBaseVisibilityUpdate,
        actor_id: int | None,
    ) -> KnowledgeBaseVisibilityUpdate:
        self.store.knowledge_bases[payload.kb_id] = payload
        self.record_audit(
            actor_id=actor_id,
            action=AuditAction.UPDATE_KB_VISIBILITY,
            resource_type=ResourceType.KNOWLEDGE_BASE.value,
            resource_id=payload.kb_id,
            detail=payload.model_dump(mode="json"),
        )
        return payload

    def check_knowledge_base_access(self, user_id: int, kb_id: int) -> PermissionDecision:
        kb = self.store.knowledge_bases.get(kb_id)
        if kb is None:
            return self.check_permission(user_id, ResourceType.KNOWLEDGE_BASE, kb_id, PermissionLevel.READ)
        if kb.owner_id == user_id or kb.visibility == KnowledgeVisibility.PUBLIC:
            return PermissionDecision(
                allowed=True,
                effective_level=PermissionLevel.READ,
                reason="knowledge base visibility",
            )
        if kb.visibility == KnowledgeVisibility.TEAM:
            user_team_ids = {
                item.team_id
                for item in self.store.user_roles
                if item.user_id == user_id and item.team_id
            }
            if kb.team_id in user_team_ids:
                return PermissionDecision(
                    allowed=True,
                    effective_level=PermissionLevel.READ,
                    reason="team visible knowledge base",
                )
        return PermissionDecision(
            allowed=False,
            effective_level=PermissionLevel.NONE,
            reason="knowledge base is not visible",
        )

    def list_audit_logs(
        self,
        actor_id: int | None = None,
        resource_type: str | None = None,
        action: str | None = None,
    ) -> list[AuditLogRead]:
        logs = self.store.audit_logs
        if actor_id is not None:
            logs = [log for log in logs if log.actor_id == actor_id]
        if resource_type is not None:
            logs = [log for log in logs if log.resource_type == resource_type]
        if action is not None:
            logs = [log for log in logs if log.action == action]
        return logs

    def record_audit(
        self,
        actor_id: int | None,
        action: AuditAction | str,
        resource_type: str,
        resource_id: int | None,
        detail: dict[str, Any],
    ) -> AuditLogRead:
        log = AuditLogRead(
            id=self.store.next_audit_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            created_at=datetime.now(timezone.utc),
        )
        self.store.audit_logs.append(log)
        self.store.next_audit_id += 1
        return log

    def _resolve_resource_level(
        self,
        user_id: int,
        role_ids: set[int],
        resource_type: ResourceType,
        resource_id: int,
    ) -> PermissionLevel:
        candidates: list[PermissionLevel] = []
        current: tuple[ResourceType, int] | None = (resource_type, resource_id)

        while current is not None:
            current_type, current_id = current
            for rule in self.store.permission_rules:
                if rule.resource_type != current_type or rule.resource_id != current_id:
                    continue
                if current != (resource_type, resource_id) and not rule.inherit:
                    continue
                user_match = rule.subject_type == "user" and rule.subject_id == user_id
                role_match = rule.subject_type == "role" and rule.subject_id in role_ids
                if user_match or role_match:
                    candidates.append(rule.level)
            current = self.store.parent_resources.get(current)

        return max(candidates, key=lambda level: LEVEL_RANK[level], default=PermissionLevel.NONE)

    def _audit_permission_check(
        self,
        actor_id: int | None,
        user_id: int,
        resource_type: ResourceType,
        resource_id: int,
        required_level: PermissionLevel,
        decision: PermissionDecision,
    ) -> None:
        self.record_audit(
            actor_id=actor_id,
            action=AuditAction.CHECK_PERMISSION,
            resource_type=resource_type.value,
            resource_id=resource_id,
            detail={
                "user_id": user_id,
                "required_level": required_level.value,
                "allowed": decision.allowed,
                "effective_level": decision.effective_level.value,
                "reason": decision.reason,
            },
        )


permission_service = PermissionService()
