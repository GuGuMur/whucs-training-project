from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v2._deps import get_svc, current_user
from app.domain.schemas import (
    UserPublic,
    WorkflowCreate,
    WorkflowDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowListResponse,
    WorkflowUpdate,
    WorkflowValidationResponse,
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
    return WorkflowListResponse(items=await svc.list_workflows())


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
) -> dict:
    return svc.start_debug(workflow_id, {}, user)


@router.post("/workflows/{workflow_id}/debug/step")
async def debug_step(
    workflow_id: str,
    body: dict,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> dict:
    return svc.step_debug(body.get("session_id", ""), workflow_id)
