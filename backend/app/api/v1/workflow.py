from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.v1.auth import current_user
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
from app.services.workspace import workspace_service

router = APIRouter()


@router.get("/workflows", response_model=WorkflowListResponse)
def workflows(_: Annotated[UserPublic, Depends(current_user)]) -> WorkflowListResponse:
    return WorkflowListResponse(items=workspace_service.list_workflows())


@router.post("/workflows", response_model=WorkflowDefinition, status_code=status.HTTP_201_CREATED)
def create_workflow(
    payload: WorkflowCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> WorkflowDefinition:
    return workspace_service.create_workflow(payload, user)


@router.patch("/workflows/{workflow_id}", response_model=WorkflowDefinition)
def update_workflow(
    workflow_id: str,
    payload: WorkflowUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> WorkflowDefinition:
    return workspace_service.update_workflow(workflow_id, payload, user)


@router.post("/workflows/{workflow_id}/validate", response_model=WorkflowValidationResponse)
def validate_workflow(
    workflow_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> WorkflowValidationResponse:
    return workspace_service.validate_workflow(workflow_id, user)


@router.post("/workflows/{workflow_id}/publish", response_model=WorkflowDefinition)
def publish_workflow(
    workflow_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> WorkflowDefinition:
    return workspace_service.publish_workflow(workflow_id, user)


@router.post(
    "/workflows/{workflow_id}/executions",
    response_model=WorkflowExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
def execute_workflow(
    workflow_id: str,
    payload: WorkflowExecutionRequest,
    user: Annotated[UserPublic, Depends(current_user)],
) -> WorkflowExecutionResponse:
    return workspace_service.execute_workflow(workflow_id, payload, user)


