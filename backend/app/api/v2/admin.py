from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.v2._deps import get_svc, current_user
from app.domain.schemas import (
    AuditLogResponse,
    NotificationItem,
    NotificationListResponse,
    PermissionRuleCreate,
    PermissionRuleListResponse,
    PermissionRulePublic,
    UserPublic,
)
from app.services.workspace_db import WorkspaceServiceDB

router = APIRouter()


@router.get("/permissions/rules", response_model=PermissionRuleListResponse)
async def permission_rules(
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> PermissionRuleListResponse:
    return PermissionRuleListResponse(items=await svc.list_permission_rules(user))


@router.post("/permissions/rules", response_model=PermissionRulePublic, status_code=status.HTTP_201_CREATED)
async def create_permission_rule(
    payload: PermissionRuleCreate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> PermissionRulePublic:
    return await svc.create_permission_rule(payload, user)


@router.delete("/permissions/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission_rule(
    rule_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> Response:
    await svc.delete_permission_rule(rule_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/notifications", response_model=NotificationListResponse)
async def notifications(
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> NotificationListResponse:
    items = await svc.list_notifications(user)
    unread_count = sum(1 for item in items if not item.is_read)
    return NotificationListResponse(items=items, total=len(items), unread_count=unread_count)


@router.patch("/notifications/{notification_id}/read", response_model=NotificationItem)
async def mark_notification_read(
    notification_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> NotificationItem:
    return await svc.mark_notification_read(notification_id, user)


@router.get("/audit-logs", response_model=AuditLogResponse)
async def audit_logs(
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> AuditLogResponse:
    return AuditLogResponse(items=await svc.list_audit_logs())
