from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    file_id: str
    document_id: str
    chunk_id: str
    title: str
    page_no: int
    paragraph_no: int
    snippet: str


class QARequest(BaseModel):
    kb_id: str
    conversation_id: str | None = None
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    stream: bool = False
    report_mode: bool = False


class QAResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    citations: list[Citation]


KnowledgeBaseStatus = Literal["active", "archived"]
KnowledgeIndexStatus = Literal["queued", "indexing", "indexed", "failed"]


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    status: KnowledgeBaseStatus | None = None


class KnowledgeBasePublic(BaseModel):
    id: str
    name: str
    description: str
    status: KnowledgeBaseStatus
    document_count: int
    chunk_count: int
    updated_at: datetime


class KnowledgeBaseListResponse(BaseModel):
    items: list[KnowledgeBasePublic]


class KnowledgeDocumentCreate(BaseModel):
    file_id: str = Field(min_length=1)


class KnowledgeDocumentPublic(BaseModel):
    id: str
    kb_id: str
    file_id: str
    file_name: str
    index_status: KnowledgeIndexStatus
    chunk_count: int
    updated_at: datetime


class KnowledgeDocumentListResponse(BaseModel):
    items: list[KnowledgeDocumentPublic]
