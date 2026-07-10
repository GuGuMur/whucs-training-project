from __future__ import annotations

from typing import Annotated
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Response, WebSocket, status

from app.api.v1.auth import current_user
from app.domain.schemas import (
    AuditLogResponse,
    NotificationItem,
    NotificationListResponse,
    PermissionRuleCreate,
    PermissionRuleListResponse,
    PermissionRulePublic,
    UserPublic,
    WorkspaceSnapshot,
)
from app.services.websocket_manager import ws_manager
from app.services.workspace import workspace_service

router = APIRouter()


@router.get("/permissions/rules", response_model=PermissionRuleListResponse)
def permission_rules(user: Annotated[UserPublic, Depends(current_user)]) -> PermissionRuleListResponse:
    return PermissionRuleListResponse(items=workspace_service.list_permission_rules(user))


@router.post("/permissions/rules", response_model=PermissionRulePublic, status_code=status.HTTP_201_CREATED)
def create_permission_rule(
    payload: PermissionRuleCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> PermissionRulePublic:
    return workspace_service.create_permission_rule(payload, user)


@router.delete("/permissions/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission_rule(rule_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> Response:
    workspace_service.delete_permission_rule(rule_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/notifications", response_model=NotificationListResponse)
def notifications(user: Annotated[UserPublic, Depends(current_user)]) -> NotificationListResponse:
    items = workspace_service.list_notifications(user)
    unread_count = sum(1 for item in items if not item.is_read)
    return NotificationListResponse(items=items, total=len(items), unread_count=unread_count)


@router.patch("/notifications/{notification_id}/read", response_model=NotificationItem)
def mark_notification_read(
    notification_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> NotificationItem:
    return workspace_service.mark_notification_read(notification_id, user)


@router.get("/audit-logs", response_model=AuditLogResponse)
def audit_logs(_: Annotated[UserPublic, Depends(current_user)]) -> AuditLogResponse:
    return AuditLogResponse(items=workspace_service.list_audit_logs())


@router.get("/workspace/snapshot", response_model=WorkspaceSnapshot)
def workspace_snapshot(user: Annotated[UserPublic, Depends(current_user)]) -> WorkspaceSnapshot:
    return workspace_service.snapshot(user)


# ── WebSocket ──────────────────────────────────────────────────────────

@router.websocket("/ws")
async def ws_connect(ws: WebSocket, token: str = ""):
    """Authenticated WebSocket for real-time push.

    Query params: token (JWT), channels (comma-separated: workflow,chat,activity)
    """
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
