from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import StreamingResponse

from app.api.v2._deps import get_svc, current_user
from app.domain.schemas import (
    AgentTaskContinueRequest,
    AgentTaskListResponse,
    AgentTaskRequest,
    AgentTaskResponse,
    AgentPlanPreviewResponse,
    KnowledgeBaseCreate,
    KnowledgeBaseListResponse,
    KnowledgeBasePublic,
    KnowledgeBaseUpdate,
    KnowledgeConversationDetailResponse,
    KnowledgeConversationListResponse,
    KnowledgeDocumentCreate,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentPublic,
    KnowledgeFileBatchRequest,
    KnowledgeFileBatchResponse,
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


@router.delete("/knowledge-bases/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> Response:
    await svc.delete_knowledge_base(kb_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/knowledge-bases/{kb_id}/documents", response_model=KnowledgeDocumentListResponse)
async def knowledge_documents(
    kb_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> KnowledgeDocumentListResponse:
    return KnowledgeDocumentListResponse(items=await svc.list_knowledge_documents(kb_id, user))


@router.get("/knowledge-bases/{kb_id}/files", response_model=KnowledgeDocumentListResponse)
async def knowledge_files(
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


@router.post("/knowledge-bases/{kb_id}/files:batch-add", response_model=KnowledgeFileBatchResponse)
async def batch_add_knowledge_files(
    kb_id: str,
    payload: KnowledgeFileBatchRequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> KnowledgeFileBatchResponse:
    return KnowledgeFileBatchResponse(**await svc.batch_add_knowledge_files(kb_id, payload, user))


@router.post("/knowledge-bases/{kb_id}/files:batch-remove", response_model=KnowledgeFileBatchResponse)
async def batch_remove_knowledge_files(
    kb_id: str,
    payload: KnowledgeFileBatchRequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> KnowledgeFileBatchResponse:
    return KnowledgeFileBatchResponse(**await svc.batch_remove_knowledge_files(kb_id, payload, user))


@router.post("/knowledge-bases/{kb_id}/reindex")
async def reindex_knowledge_base(
    kb_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> dict:
    return await svc.reindex_knowledge_base(kb_id, user)


@router.get("/knowledge-bases/{kb_id}/conversations", response_model=KnowledgeConversationListResponse)
async def knowledge_conversations(
    kb_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> KnowledgeConversationListResponse:
    return await svc.list_knowledge_conversations(kb_id, user)


@router.get("/conversations/{conversation_id}", response_model=KnowledgeConversationDetailResponse)
async def knowledge_conversation_detail(
    conversation_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> KnowledgeConversationDetailResponse:
    return await svc.get_knowledge_conversation(conversation_id, user)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_conversation(
    conversation_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> Response:
    await svc.delete_knowledge_conversation(conversation_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/knowledge-bases/{kb_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_knowledge_document(
    kb_id: str,
    doc_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> None:
    await svc.remove_knowledge_document(kb_id, doc_id, user)


@router.post("/qa/query", response_model=QAResponse)
async def qa_query(
    payload: QARequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> QAResponse:
    return await svc.answer_question(payload, user)


@router.post("/qa/query/stream")
async def qa_query_stream(
    payload: QARequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
):
    return StreamingResponse(
        svc.answer_question_stream(payload, user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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


@router.post("/agents/tasks/plan", response_model=AgentPlanPreviewResponse)
async def preview_agent_plan(
    payload: AgentTaskRequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> AgentPlanPreviewResponse:
    return await svc.preview_agent_plan(payload, user)


@router.post("/agents/tasks/stream")
async def stream_agent_task(
    payload: AgentTaskRequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
):
    return StreamingResponse(
        svc.stream_agent_task(payload, user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/agents/tasks", response_model=AgentTaskListResponse)
async def list_agent_tasks(
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> AgentTaskListResponse:
    return await svc.list_agent_tasks(user)


@router.get("/agents/tasks/{task_id}", response_model=AgentTaskResponse)
async def get_agent_task(
    task_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> AgentTaskResponse:
    return await svc.get_agent_task(task_id, user)


@router.delete("/agents/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_task(
    task_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> Response:
    await svc.delete_agent_task(task_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/agents/tasks/{task_id}/continue", response_model=AgentTaskResponse)
async def continue_agent_task(
    task_id: str,
    payload: AgentTaskContinueRequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> AgentTaskResponse:
    return await svc.continue_agent_task(task_id, payload, user)


@router.post("/agents/tasks/{task_id}/cancel", response_model=AgentTaskResponse)
async def cancel_agent_task(
    task_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> AgentTaskResponse:
    return await svc.cancel_agent_task(task_id, user)
