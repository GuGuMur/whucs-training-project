from typing import Annotated

from fastapi import APIRouter, Body, Depends, status

from app.api.v2._deps import get_svc, current_user
from app.domain.schemas import (
    UserPublic,
    WorkflowCreate,
    WorkflowDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowExecutionListResponse,
    WorkflowListResponse,
    WorkflowUpdate,
    WorkflowValidationResponse,
    WorkflowVersionListResponse,
)
from app.services.workspace_db import WorkspaceServiceDB

router = APIRouter()


@router.post("/workflows", response_model=WorkflowDefinition, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowCreate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> WorkflowDefinition:
    return await svc.create_workflow(payload, user)


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> WorkflowListResponse:
    return WorkflowListResponse(items=await svc.list_workflows(user))


@router.get("/workflows/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow(
    workflow_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> WorkflowDefinition:
    return await svc.get_workflow(workflow_id, user)


@router.patch("/workflows/{workflow_id}", response_model=WorkflowDefinition)
async def update_workflow(
    workflow_id: str,
    payload: WorkflowUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> WorkflowDefinition:
    return await svc.update_workflow(workflow_id, payload, user)


@router.post("/workflows/{workflow_id}/validate", response_model=WorkflowValidationResponse)
async def validate_workflow(
    workflow_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> WorkflowValidationResponse:
    return await svc.validate_workflow(workflow_id, user)


@router.post("/workflows/{workflow_id}/publish", response_model=WorkflowDefinition)
async def publish_workflow(
    workflow_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> WorkflowDefinition:
    return await svc.publish_workflow(workflow_id, user)


@router.get("/workflows/{workflow_id}/versions", response_model=WorkflowVersionListResponse)
async def list_workflow_versions(
    workflow_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> WorkflowVersionListResponse:
    return WorkflowVersionListResponse(items=await svc.list_workflow_versions(workflow_id, user))


@router.post("/workflows/{workflow_id}/versions/{version_id}/restore", response_model=WorkflowDefinition)
async def restore_workflow_version(
    workflow_id: str,
    version_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> WorkflowDefinition:
    return await svc.restore_workflow_version(workflow_id, version_id, user)


@router.get("/workflows/{workflow_id}/executions", response_model=WorkflowExecutionListResponse)
async def list_workflow_executions(
    workflow_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> WorkflowExecutionListResponse:
    return WorkflowExecutionListResponse(items=await svc.list_workflow_executions(workflow_id, user))


@router.post(
    "/workflows/{workflow_id}/executions",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def execute_workflow(
    workflow_id: str,
    payload: WorkflowExecutionRequest,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> WorkflowExecutionResponse:
    return await svc.execute_workflow(workflow_id, payload, user)

# ── Debug (FR-W07) ──
@router.post("/workflows/{workflow_id}/debug/start")
async def debug_start(
    workflow_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
    payload: WorkflowExecutionRequest = Body(default_factory=WorkflowExecutionRequest),
) -> dict:
    return await svc.start_debug(workflow_id, payload.model_dump(), user)


@router.post("/workflows/{workflow_id}/debug/step")
async def debug_step(
    workflow_id: str,
    body: dict,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> dict:
    return await svc.step_debug(body.get("session_id", ""), workflow_id, user)


@router.delete("/workflows/{workflow_id}/debug/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def debug_cancel(
    workflow_id: str,
    session_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> None:
    await svc.cancel_debug(session_id, workflow_id, user)
