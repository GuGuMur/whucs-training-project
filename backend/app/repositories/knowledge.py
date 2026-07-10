from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import KnowledgeBase, KnowledgeDocument, KnowledgeChunk

class KnowledgeBaseRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_id(self, kid: str) -> KnowledgeBase | None: return await self._s.get(KnowledgeBase, kid)
    async def list_all(self) -> list[KnowledgeBase]:
        r = await self._s.execute(select(KnowledgeBase).where(KnowledgeBase.status == "active"))
        return list(r.scalars().all())
    async def create(self, kb: KnowledgeBase) -> KnowledgeBase: self._s.add(kb); await self._s.flush(); return kb
    async def update(self, kb: KnowledgeBase) -> KnowledgeBase: await self._s.flush(); return kb

class KnowledgeDocumentRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_kb(self, kb_id: str) -> list[KnowledgeDocument]:
        r = await self._s.execute(select(KnowledgeDocument).where(KnowledgeDocument.kb_id == kb_id))
        return list(r.scalars().all())
    async def create(self, doc: KnowledgeDocument) -> KnowledgeDocument: self._s.add(doc); await self._s.flush(); return doc
    async def get_by_id(self, did: str) -> KnowledgeDocument | None: return await self._s.get(KnowledgeDocument, did)

class KnowledgeChunkRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_document(self, doc_id: str) -> list[KnowledgeChunk]:
        r = await self._s.execute(select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc_id))
        return list(r.scalars().all())
    async def create(self, chunk: KnowledgeChunk) -> KnowledgeChunk: self._s.add(chunk); await self._s.flush(); return chunk
    async def create_bulk(self, chunks: list[KnowledgeChunk]) -> None:
        self._s.add_all(chunks); await self._s.flush()
