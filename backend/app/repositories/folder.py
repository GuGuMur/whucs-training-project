from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Folder

class FolderRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_id(self, fid: str) -> Folder | None: return await self._s.get(Folder, fid)
    async def list_all(self) -> list[Folder]:
        r = await self._s.execute(select(Folder))
        return list(r.scalars().all())
    async def list_roots(self) -> list[Folder]:
        r = await self._s.execute(select(Folder).where(Folder.parent_id == None))
        return list(r.scalars().all())
    async def list_children(self, parent_id: str) -> list[Folder]:
        r = await self._s.execute(select(Folder).where(Folder.parent_id == parent_id))
        return list(r.scalars().all())
    async def create(self, f: Folder) -> Folder: self._s.add(f); await self._s.flush(); return f
    async def update(self, f: Folder) -> Folder: await self._s.flush(); return f
    async def delete(self, f: Folder) -> None: await self._s.delete(f); await self._s.flush()
