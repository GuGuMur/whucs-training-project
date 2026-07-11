from __future__ import annotations
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    KnowledgeBase,
    KnowledgeCitationSnapshot,
    KnowledgeChunk,
    KnowledgeConversation,
    KnowledgeDocument,
    KnowledgeMessage,
)

class KnowledgeBaseRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_id(self, kid: str) -> KnowledgeBase | None: return await self._s.get(KnowledgeBase, kid)
    async def list_all(self) -> list[KnowledgeBase]:
        r = await self._s.execute(select(KnowledgeBase).where(KnowledgeBase.status != "deleted"))
        return list(r.scalars().all())
    async def create(self, kb: KnowledgeBase) -> KnowledgeBase: self._s.add(kb); await self._s.flush(); return kb
    async def update(self, kb: KnowledgeBase) -> KnowledgeBase: await self._s.flush(); return kb

class KnowledgeDocumentRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_kb(self, kb_id: str) -> list[KnowledgeDocument]:
        r = await self._s.execute(
            select(KnowledgeDocument)
            .where(KnowledgeDocument.kb_id == kb_id)
            .order_by(KnowledgeDocument.updated_at, KnowledgeDocument.id)
        )
        return list(r.scalars().all())
    async def create(self, doc: KnowledgeDocument) -> KnowledgeDocument: self._s.add(doc); await self._s.flush(); return doc
    async def get_by_id(self, did: str) -> KnowledgeDocument | None: return await self._s.get(KnowledgeDocument, did)
    async def delete(self, doc: KnowledgeDocument) -> None: await self._s.delete(doc); await self._s.flush()

class KnowledgeChunkRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_document(self, doc_id: str) -> list[KnowledgeChunk]:
        r = await self._s.execute(select(KnowledgeChunk).where(KnowledgeChunk.document_id == doc_id))
        return list(r.scalars().all())
    async def create(self, chunk: KnowledgeChunk) -> KnowledgeChunk: self._s.add(chunk); await self._s.flush(); return chunk
    async def create_bulk(self, chunks: list[KnowledgeChunk]) -> None:
        self._s.add_all(chunks); await self._s.flush()
    async def delete_by_document(self, doc_id: str) -> None:
        await self._s.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == doc_id))
        await self._s.flush()

class KnowledgeConversationRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_id(self, conversation_id: str) -> KnowledgeConversation | None:
        return await self._s.get(KnowledgeConversation, conversation_id)
    async def list_by_kb(self, kb_id: str) -> list[KnowledgeConversation]:
        r = await self._s.execute(
            select(KnowledgeConversation)
            .where(KnowledgeConversation.kb_id == kb_id)
            .order_by(KnowledgeConversation.updated_at.desc())
        )
        return list(r.scalars().all())
    async def create(self, conversation: KnowledgeConversation) -> KnowledgeConversation:
        self._s.add(conversation); await self._s.flush(); return conversation
    async def update(self, conversation: KnowledgeConversation) -> KnowledgeConversation:
        await self._s.flush(); return conversation
    async def delete(self, conversation: KnowledgeConversation) -> None:
        await self._s.delete(conversation); await self._s.flush()

class KnowledgeMessageRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_conversation(self, conversation_id: str) -> list[KnowledgeMessage]:
        r = await self._s.execute(
            select(KnowledgeMessage)
            .where(KnowledgeMessage.conversation_id == conversation_id)
            .order_by(KnowledgeMessage.created_at)
        )
        return list(r.scalars().all())
    async def create(self, message: KnowledgeMessage) -> KnowledgeMessage:
        self._s.add(message); await self._s.flush(); return message
    async def delete_by_conversation(self, conversation_id: str) -> None:
        await self._s.execute(delete(KnowledgeMessage).where(KnowledgeMessage.conversation_id == conversation_id))
        await self._s.flush()

class KnowledgeCitationSnapshotRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_message(self, message_id: str) -> list[KnowledgeCitationSnapshot]:
        r = await self._s.execute(
            select(KnowledgeCitationSnapshot)
            .where(KnowledgeCitationSnapshot.message_id == message_id)
            .order_by(KnowledgeCitationSnapshot.ordinal)
        )
        return list(r.scalars().all())
    async def create_bulk(self, snapshots: list[KnowledgeCitationSnapshot]) -> None:
        self._s.add_all(snapshots); await self._s.flush()
    async def delete_by_message_ids(self, message_ids: list[str]) -> None:
        if not message_ids:
            return
        await self._s.execute(delete(KnowledgeCitationSnapshot).where(KnowledgeCitationSnapshot.message_id.in_(message_ids)))
        await self._s.flush()
