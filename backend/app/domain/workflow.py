from __future__ import annotations

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


class AgentStep(BaseModel):
    type: Literal["thought", "action", "observation", "answer"]
    title: str
    content: str
    tool_name: str | None = None
    status: Literal["pending", "running", "success", "failed"] = "success"
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentTaskResponse(BaseModel):
    id: str
    task: str
    status: Literal["queued", "running", "completed", "failed"]
    steps: list[AgentStep]
    final_answer: str


WorkflowNodeType = Literal["trigger", "tool",
                           "condition", "loop", "aggregate", "output"]


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


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    trigger: str = Field(default="manual", min_length=1, max_length=80)
    nodes: list[WorkflowNodeDefinition] = Field(default_factory=list)
    edges: list[WorkflowEdgeDefinition] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
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
    nodes: list[WorkflowNodeDefinition] = Field(default_factory=list)
    edges: list[WorkflowEdgeDefinition] = Field(default_factory=list)


class WorkflowListResponse(BaseModel):
    items: list[WorkflowDefinition]


class WorkflowExecutionRequest(BaseModel):
    file_id: str
    target_kb_id: str | None = None


class WorkflowNodeExecution(BaseModel):
    node_id: str
    name: str
    tool_name: str
    status: Literal["pending", "running", "success", "failed"]
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    status: Literal["queued", "running", "completed", "failed"]
    node_executions: list[WorkflowNodeExecution]
    output: dict[str, Any]
