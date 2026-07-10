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
    error_code: Literal["KB_EMPTY", "KB_FILE_NOT_INDEXED", "KB_NO_MATCH"] | None = None


KnowledgeScopeType = Literal["personal", "team"]
KnowledgeBaseStatus = Literal["active", "archived", "deleted"]
KnowledgeFreshnessPolicy = Literal["manual", "on_file_update"]
KnowledgeIndexStatus = Literal["queued", "indexing", "indexed", "failed"]


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    scope_type: KnowledgeScopeType = "personal"
    scope_id: str | None = None
    category: str | None = Field(default=None, max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=20)
    freshness_policy: KnowledgeFreshnessPolicy = "manual"


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    status: KnowledgeBaseStatus | None = None
    category: str | None = Field(default=None, max_length=80)
    tags: list[str] | None = Field(default=None, max_length=20)
    freshness_policy: KnowledgeFreshnessPolicy | None = None


class KnowledgeBasePublic(BaseModel):
    id: str
    name: str
    description: str
    scope_type: KnowledgeScopeType = "personal"
    scope_id: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    freshness_policy: KnowledgeFreshnessPolicy = "manual"
    status: KnowledgeBaseStatus
    document_count: int
    chunk_count: int
    last_indexed_at: datetime | None = None
    updated_at: datetime


class KnowledgeBaseListResponse(BaseModel):
    items: list[KnowledgeBasePublic]


class KnowledgeDocumentCreate(BaseModel):
    file_id: str = Field(min_length=1)


class KnowledgeFileBatchRequest(BaseModel):
    file_ids: list[str] = Field(min_length=1, max_length=100)


class KnowledgeDocumentPublic(BaseModel):
    id: str
    kb_id: str
    file_id: str
    file_name: str
    index_status: KnowledgeIndexStatus
    chunk_count: int
    error_message: str | None = None
    updated_at: datetime


class KnowledgeDocumentListResponse(BaseModel):
    items: list[KnowledgeDocumentPublic]


class KnowledgeFileBatchResponse(BaseModel):
    added: list[KnowledgeDocumentPublic] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    skipped: list[dict[str, str]] = Field(default_factory=list)


class KnowledgeConversationPublic(BaseModel):
    id: str
    kb_id: str
    title: str
    message_count: int
    updated_at: datetime


class KnowledgeMessagePublic(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime


class KnowledgeConversationListResponse(BaseModel):
    items: list[KnowledgeConversationPublic]


class KnowledgeConversationDetailResponse(BaseModel):
    conversation: KnowledgeConversationPublic
    messages: list[KnowledgeMessagePublic]
