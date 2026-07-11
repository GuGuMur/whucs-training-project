"""v2 WebSocket endpoint for real-time team chat, notifications, and activity."""

from urllib.parse import parse_qs

from fastapi import APIRouter, WebSocket

from app.core.database import async_session
from app.services.websocket_manager import ws_manager
from app.services.workspace_db import WorkspaceServiceDB

router = APIRouter()


@router.websocket("/ws")
async def ws_connect(ws: WebSocket, token: str = ""):
    """Authenticated WebSocket for real-time push.

    Query params: token (JWT), channels (comma-separated)
    Auto-subscribes to user-{id} and team-{id} for each team the user belongs to.
    """
    qs = parse_qs(ws.scope.get("query_string", b"").decode())
    token = qs.get("token", [""])[0]
    channels_str = qs.get("channels", ["workflow"])[0]
    channels = [c.strip() for c in channels_str.split(",") if c.strip()]

    # Authenticate via DB-backed v2 service
    async with async_session() as session:
        svc = WorkspaceServiceDB(session)
        try:
            user = await svc.require_user(f"Bearer {token}")
        except Exception:
            await ws.close(code=4001)
            return

        # Subscribe to user's personal channel + team channels they belong to
        channels.append(f"user-{user.id}")
        teams = await svc.list_teams(user)
        for team in teams:
            channels.append(f"team-{team.id}")

    await ws_manager.connect(ws, channels)
    try:
        while True:
            await ws.receive_text()
    except Exception:
        pass
    finally:
        await ws_manager.disconnect(ws)
