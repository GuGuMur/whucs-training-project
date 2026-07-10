from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v2._deps import get_svc, current_user
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
from app.services.workspace_db import WorkspaceServiceDB

router = APIRouter()


@router.post("/knowledge-bases", response_model=KnowledgeBasePublic, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> KnowledgeBasePublic:
    return await svc.create_knowledge_base(payload, user)


@router.get("/knowledge-bases", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> KnowledgeBaseListResponse:
    return KnowledgeBaseListResponse(items=await svc.list_knowledge_bases(user))


@router.patch("/knowledge-bases/{kb_id}", response_model=KnowledgeBasePublic)
async def update_knowledge_base(
    kb_id: str,
    payload: KnowledgeBaseUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> KnowledgeBasePublic:
    return await svc.update_knowledge_base(kb_id, payload, user)


@router.get("/knowledge-bases/{kb_id}/documents", response_model=KnowledgeDocumentListResponse)
async def knowledge_documents(
    kb_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> KnowledgeDocumentListResponse:
    return KnowledgeDocumentListResponse(items=await svc.list_knowledge_documents(kb_id, user))


@router.post(
    "/knowledge-bases/{kb_id}/documents",
    response_model=KnowledgeDocumentPublic,
    status_code=status.HTTP_201_CREATED,
)
async def add_knowledge_document(
    kb_id: str,
    payload: KnowledgeDocumentCreate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> KnowledgeDocumentPublic:
    return await svc.add_knowledge_document(kb_id, payload, user)


@router.post("/qa/query", response_model=QAResponse)
async def qa_query(
    payload: QARequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> QAResponse:
    return await svc.answer_question(payload, user)


@router.get("/tools", response_model=ToolListResponse)
async def tools(
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> ToolListResponse:
    return ToolListResponse(items=await svc.list_tools())


@router.post("/agents/tasks", response_model=AgentTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_task(
    payload: AgentTaskRequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> AgentTaskResponse:
    return await svc.create_agent_task(payload, user)
