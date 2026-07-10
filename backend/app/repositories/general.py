from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import PermissionRule, Notification, AuditLog, Conversation, MultipartUpload

class PermissionRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_all(self) -> list[PermissionRule]:
        r = await self._s.execute(select(PermissionRule))
        return list(r.scalars().all())
    async def create(self, rule: PermissionRule) -> PermissionRule: self._s.add(rule); await self._s.flush(); return rule
    async def delete(self, rule: PermissionRule) -> None: await self._s.delete(rule); await self._s.flush()
    async def get_by_id(self, rid: str) -> PermissionRule | None: return await self._s.get(PermissionRule, rid)

class NotificationRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_user(self, user_id: int) -> list[Notification]:
        r = await self._s.execute(select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc()))
        return list(r.scalars().all())
    async def create(self, n: Notification) -> Notification: self._s.add(n); await self._s.flush(); return n
    async def get_by_id(self, nid: str) -> Notification | None: return await self._s.get(Notification, nid)

class AuditLogRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_recent(self, limit: int = 100) -> list[AuditLog]:
        r = await self._s.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
        return list(r.scalars().all())
    async def create(self, log: AuditLog) -> AuditLog: self._s.add(log); await self._s.flush(); return log

class ConversationRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_session(self, session_id: str) -> list[Conversation]:
        r = await self._s.execute(select(Conversation).where(Conversation.session_id == session_id).order_by(Conversation.created_at))
        return list(r.scalars().all())
    async def create(self, conv: Conversation) -> Conversation: self._s.add(conv); await self._s.flush(); return conv

class MultipartUploadRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_id(self, uid: str) -> MultipartUpload | None: return await self._s.get(MultipartUpload, uid)
    async def create(self, mu: MultipartUpload) -> MultipartUpload: self._s.add(mu); await self._s.flush(); return mu
    async def delete(self, mu: MultipartUpload) -> None: await self._s.delete(mu); await self._s.flush()
