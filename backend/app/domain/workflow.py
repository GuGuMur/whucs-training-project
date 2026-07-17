from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    id: str
    name: str
    version: str
    category: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    enabled: bool = True


class ToolListResponse(BaseModel):
    items: list[ToolDefinition]


class AgentTaskRequest(BaseModel):
    task: str = Field(min_length=1)
    kb_id: str | None = None
    context_file_ids: list[str] = Field(default_factory=list)


class AgentPlanPreviewStep(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""
    risk_level: Literal["low", "medium", "high"] = "low"
    risk_reason: str = ""


class AgentPlanPreviewResponse(BaseModel):
    intent: str
    missing_fields: list[str] = Field(default_factory=list)
    answer_strategy: str = "direct"
    risk_level: Literal["low", "medium", "high"] = "low"
    risk_reason: str = ""
    requires_confirmation: bool = False
    steps: list[AgentPlanPreviewStep] = Field(default_factory=list)


class AgentTaskContinueRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)
    message: str | None = Field(default=None, min_length=1, max_length=4000)


class AgentStep(BaseModel):
    type: Literal["thought", "action", "observation", "answer"]
    phase: Literal["understand", "plan", "call", "observe", "answer"] = "answer"
    title: str
    content: str
    tool_name: str | None = None
    input_json: dict[str, Any] = Field(default_factory=dict)
    output_json: dict[str, Any] = Field(default_factory=dict)
    status: Literal["pending", "running", "success", "failed", "needs_clarification"] = "success"
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentMessage(BaseModel):
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentToolCall(BaseModel):
    id: str
    tool_name: str
    input_json: dict[str, Any] = Field(default_factory=dict)
    output_json: dict[str, Any] = Field(default_factory=dict)
    status: Literal["success", "failed", "needs_clarification"] = "success"
    error_message: str | None = None
    latency_ms: int = 0


class AgentPlanRevision(BaseModel):
    id: str
    revision_no: int
    reason: str
    plan_json: dict[str, Any] = Field(default_factory=dict)


class AgentTaskResponse(BaseModel):
    id: str
    task: str
    status: Literal["queued", "running", "completed", "failed", "needs_clarification", "cancelled"]
    steps: list[AgentStep]
    final_answer: str
    result_view: dict[str, Any] = Field(default_factory=dict)
    messages: list[AgentMessage] = Field(default_factory=list)
    tool_calls: list[AgentToolCall] = Field(default_factory=list)
    plan_revisions: list[AgentPlanRevision] = Field(default_factory=list)


class AgentTaskListResponse(BaseModel):
    items: list[AgentTaskResponse]


WorkflowNodeType = Literal[
    "input",
    "trigger",
    "tool",
    "condition",
    "loop",
    "transform",
    "aggregate",
    "output",
]


class WorkflowNodeDefinition(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    type: WorkflowNodeType
    tool_name: str | None = Field(default=None, max_length=80)
    parameters: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, float] = Field(default_factory=dict)


class WorkflowEdgeDefinition(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    source: str = Field(min_length=1, max_length=64)
    target: str = Field(min_length=1, max_length=64)
    source_handle: str | None = None
    target_handle: str | None = None
    label: str | None = Field(default=None, max_length=128)
    type: str | None = Field(default=None, max_length=32)


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    trigger: str = Field(default="manual", min_length=1, max_length=80)
    nodes: list[WorkflowNodeDefinition] = Field(default_factory=list)
    edges: list[WorkflowEdgeDefinition] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    expected_revision: int | None = Field(default=None, ge=0)
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    trigger: str | None = Field(default=None, min_length=1, max_length=80)
    nodes: list[WorkflowNodeDefinition] | None = None
    edges: list[WorkflowEdgeDefinition] | None = None


class WorkflowValidationIssue(BaseModel):
    code: str
    message: str
    node_id: str | None = None
    edge_id: str | None = None


class WorkflowValidationResponse(BaseModel):
    valid: bool
    issues: list[WorkflowValidationIssue]
    node_count: int
    edge_count: int


class WorkflowDefinition(BaseModel):
    id: str
    name: str
    description: str
    trigger: str
    version: str
    node_count: int
    status: Literal["draft", "published", "template"]
    revision: int = 0
    nodes: list[WorkflowNodeDefinition] = Field(default_factory=list)
    edges: list[WorkflowEdgeDefinition] = Field(default_factory=list)


class WorkflowListResponse(BaseModel):
    items: list[WorkflowDefinition]


class WorkflowExecutionRequest(BaseModel):
    file_id: str | None = None
    target_kb_id: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)


class WorkflowNodeExecution(BaseModel):
    node_id: str
    name: str
    tool_name: str
    status: Literal["pending", "running", "success", "failed", "skipped"]
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    status: Literal["queued", "running", "completed", "failed"]
    node_executions: list[WorkflowNodeExecution]
    output: dict[str, Any]


class WorkflowVersionPublic(BaseModel):
    id: str
    workflow_id: str
    version: str
    name: str
    description: str
    trigger: str
    nodes: list[WorkflowNodeDefinition] = Field(default_factory=list)
    edges: list[WorkflowEdgeDefinition] = Field(default_factory=list)
    published_at: datetime


class WorkflowVersionListResponse(BaseModel):
    items: list[WorkflowVersionPublic]


class WorkflowExecutionRecord(BaseModel):
    id: str
    workflow_id: str
    workflow_version: str
    status: Literal["queued", "running", "completed", "failed"]
    node_executions: list[WorkflowNodeExecution] = Field(default_factory=list)
    output: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class WorkflowExecutionListResponse(BaseModel):
    items: list[WorkflowExecutionRecord]
