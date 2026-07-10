from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Workflow

class WorkflowRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_id(self, wid: str) -> Workflow | None: return await self._s.get(Workflow, wid)
    async def list_all(self) -> list[Workflow]:
        r = await self._s.execute(select(Workflow))
        return list(r.scalars().all())
    async def create(self, w: Workflow) -> Workflow: self._s.add(w); await self._s.flush(); return w
    async def update(self, w: Workflow) -> Workflow: await self._s.flush(); return w
    async def delete(self, w: Workflow) -> None: await self._s.delete(w); await self._s.flush()
