from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.api.v1.auth import current_user
from app.domain.schemas import (
    AgentTaskRequest,
    AgentTaskResponse,
    KnowledgeBaseCreate,
    KnowledgeBaseListResponse,
    KnowledgeBasePublic,
    KnowledgeBaseUpdate,
    KnowledgeDocumentCreate,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentPublic,
    QARequest,
    QAResponse,
    ToolListResponse,
    UserPublic,
)
from app.services.llm import generate_rag_answer_stream
from app.services.workspace import workspace_service

router = APIRouter()


@router.get("/knowledge-bases", response_model=KnowledgeBaseListResponse)
def knowledge_bases(user: Annotated[UserPublic, Depends(current_user)]) -> KnowledgeBaseListResponse:
    return KnowledgeBaseListResponse(items=workspace_service.list_knowledge_bases(user))


@router.post("/knowledge-bases", response_model=KnowledgeBasePublic, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> KnowledgeBasePublic:
    return workspace_service.create_knowledge_base(payload, user)


@router.patch("/knowledge-bases/{kb_id}", response_model=KnowledgeBasePublic)
def update_knowledge_base(
    kb_id: str,
    payload: KnowledgeBaseUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> KnowledgeBasePublic:
    return workspace_service.update_knowledge_base(kb_id, payload, user)


@router.get("/knowledge-bases/{kb_id}/documents", response_model=KnowledgeDocumentListResponse)
def knowledge_documents(
    kb_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> KnowledgeDocumentListResponse:
    return KnowledgeDocumentListResponse(items=workspace_service.list_knowledge_documents(kb_id, user))


@router.post(
    "/knowledge-bases/{kb_id}/documents",
    response_model=KnowledgeDocumentPublic,
    status_code=status.HTTP_201_CREATED,
)
def add_knowledge_document(
    kb_id: str,
    payload: KnowledgeDocumentCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> KnowledgeDocumentPublic:
    return workspace_service.add_knowledge_document(kb_id, payload, user)


@router.post("/qa/query", response_model=QAResponse)
def qa_query(payload: QARequest, user: Annotated[UserPublic, Depends(current_user)]) -> QAResponse:
    return workspace_service.answer_question(payload, user)


@router.post("/qa/query/stream")
async def qa_query_stream(payload: QARequest, user: Annotated[UserPublic, Depends(current_user)]):
    """Streaming QA endpoint using Server-Sent Events."""
    citations = workspace_service._retrieve_knowledge_citations(
        payload.kb_id, payload.question, payload.top_k, user,
    )
    snippets = [c.snippet for c in citations[:5]]
    kb_name = workspace_service._knowledge_bases.get(payload.kb_id)
    kb_label = kb_name.name if kb_name else payload.kb_id

    async def event_stream():
        for chunk in generate_rag_answer_stream(payload.question, snippets, kb_label):
            yield f"data: {chunk}\n\n"
        # Send citations as final event
        citation_data = json.dumps(
            [{"title": c.title, "snippet": c.snippet, "page_no": c.page_no} for c in citations],
            ensure_ascii=False,
        )
        yield f"event: citations\ndata: {citation_data}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/tools", response_model=ToolListResponse)
def tools(_: Annotated[UserPublic, Depends(current_user)]) -> ToolListResponse:
    return ToolListResponse(items=workspace_service.list_tools())


@router.post("/agents/tasks", response_model=AgentTaskResponse, status_code=status.HTTP_201_CREATED)
def create_agent_task(
    payload: AgentTaskRequest,
    user: Annotated[UserPublic, Depends(current_user)],
) -> AgentTaskResponse:
    return workspace_service.create_agent_task(payload, user)
