from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    scope_type: Mapped[str] = mapped_column(String(16), default="personal", index=True)
    scope_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(80), default="")
    tags: Mapped[str] = mapped_column(Text, default="[]")
    freshness_policy: Mapped[str] = mapped_column(String(32), default="manual")
    status: Mapped[str] = mapped_column(String(16), default="active")  # active/archived/deleted
    last_indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kb_id: Mapped[str] = mapped_column(String(64), ForeignKey("knowledge_bases.id"), index=True)
    file_id: Mapped[str] = mapped_column(String(64), ForeignKey("files.id"))
    file_name: Mapped[str] = mapped_column(String(512))
    version_sha: Mapped[str] = mapped_column(String(64), default="")
    index_status: Mapped[str] = mapped_column(String(16), default="indexed")  # queued/indexed/failed
    error_message: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(64), ForeignKey("knowledge_documents.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    page_no: Mapped[int] = mapped_column(Integer, default=1)
    paragraph_no: Mapped[int] = mapped_column(Integer, default=1)
    embedding_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Milvus ID


class KnowledgeConversation(Base):
    __tablename__ = "knowledge_conversations"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kb_id: Mapped[str] = mapped_column(String(64), ForeignKey("knowledge_bases.id"), index=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class KnowledgeMessage(Base):
    __tablename__ = "knowledge_messages"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(64), ForeignKey("knowledge_conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class KnowledgeCitationSnapshot(Base):
    __tablename__ = "knowledge_citation_snapshots"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    message_id: Mapped[str] = mapped_column(String(64), ForeignKey("knowledge_messages.id"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer, default=0)
    file_id: Mapped[str] = mapped_column(String(64))
    document_id: Mapped[str] = mapped_column(String(64))
    chunk_id: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(512), default="")
    page_no: Mapped[int] = mapped_column(Integer, default=1)
    paragraph_no: Mapped[int] = mapped_column(Integer, default=1)
    snippet: Mapped[str] = mapped_column(Text)


# ── Workflow ──
