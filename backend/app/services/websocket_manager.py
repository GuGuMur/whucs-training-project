"""WebSocket connection manager for real-time push.

Handles authenticated connections, channel subscriptions, and broadcasting
for workflow progress, team chat, and activity feed events.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}
        self._ws_channels: dict[WebSocket, set[str]] = {}

    async def connect(self, ws: WebSocket, channels: list[str]) -> None:
        await ws.accept()
        self._ws_channels[ws] = set(channels)
        for ch in channels:
            self._connections.setdefault(ch, []).append(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        channels = self._ws_channels.pop(ws, set())
        for ch in channels:
            conns = self._connections.get(ch, [])
            if ws in conns:
                conns.remove(ws)

    async def broadcast(self, channel: str, event: str, data: dict[str, Any]) -> None:
        payload = json.dumps({"event": event, "data": data}, ensure_ascii=False)
        dead: list[WebSocket] = []
        for ws in self._connections.get(channel, []):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)


ws_manager = WebSocketManager()
