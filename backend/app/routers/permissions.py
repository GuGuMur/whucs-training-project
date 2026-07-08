from fastapi import APIRouter, Header, HTTPException, Query, status

from app.security.schemas import (
    AuditLogRead,
    KnowledgeBaseVisibilityUpdate,
    PermissionCheck,
    PermissionDecision,
    PermissionGrant,
    ResourceParentSet,
    RoleCreate,
    RoleRead,
    ToolPermissionGrant,
    UserRoleAssign,
)
from app.security.service import permission_service


router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> RoleRead:
    return permission_service.create_role(payload, actor_id=x_user_id)


@router.get("/roles", response_model=list[RoleRead])
async def list_roles() -> list[RoleRead]:
    return permission_service.list_roles()


@router.post("/roles/assign", response_model=UserRoleAssign)
async def assign_role(
    payload: UserRoleAssign,
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> UserRoleAssign:
    try:
        return permission_service.assign_role(payload, actor_id=x_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/resources/grants", response_model=PermissionGrant)
async def grant_resource_permission(
    payload: PermissionGrant,
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> PermissionGrant:
    return permission_service.grant_permission(payload, actor_id=x_user_id)


@router.post("/resources/parents", response_model=ResourceParentSet)
async def set_resource_parent(
    payload: ResourceParentSet,
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> ResourceParentSet:
    return permission_service.set_resource_parent(payload, actor_id=x_user_id)


@router.post("/resources/check", response_model=PermissionDecision)
async def check_resource_permission(
    payload: PermissionCheck,
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> PermissionDecision:
    return permission_service.check_permission(
        user_id=payload.user_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        required_level=payload.required_level,
        actor_id=x_user_id,
    )


@router.post("/tools/grants", response_model=ToolPermissionGrant)
async def grant_tool_permission(
    payload: ToolPermissionGrant,
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> ToolPermissionGrant:
    return permission_service.grant_tool_permission(payload, actor_id=x_user_id)


@router.get("/tools/{tool_id}/users/{user_id}/check", response_model=PermissionDecision)
async def check_tool_permission(tool_id: int, user_id: int) -> PermissionDecision:
    return permission_service.can_execute_tool(user_id=user_id, tool_id=tool_id)


@router.put("/knowledge-bases/{kb_id}/visibility", response_model=KnowledgeBaseVisibilityUpdate)
async def update_knowledge_base_visibility(
    kb_id: int,
    payload: KnowledgeBaseVisibilityUpdate,
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> KnowledgeBaseVisibilityUpdate:
    if kb_id != payload.kb_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="path kb_id must match payload kb_id",
        )
    return permission_service.update_kb_visibility(payload, actor_id=x_user_id)


@router.get("/knowledge-bases/{kb_id}/users/{user_id}/check", response_model=PermissionDecision)
async def check_knowledge_base_access(kb_id: int, user_id: int) -> PermissionDecision:
    return permission_service.check_knowledge_base_access(user_id=user_id, kb_id=kb_id)


@router.get("/audit-logs", response_model=list[AuditLogRead])
async def list_audit_logs(
    actor_id: int | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    action: str | None = Query(default=None),
) -> list[AuditLogRead]:
    return permission_service.list_audit_logs(
        actor_id=actor_id,
        resource_type=resource_type,
        action=action,
    )
