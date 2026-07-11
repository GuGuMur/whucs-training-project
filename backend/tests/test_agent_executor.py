from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

from app.domain.schemas import UserPublic
from app.services.agent_executor import AgentExecutor
from app.services.agent_planner import AgentPlan, PlannedToolCall
from app.services.tool_registry import ToolExecution


class _FakePlanner:
    def __init__(self, initial: AgentPlan, revisions: list[AgentPlan] | None = None) -> None:
        self.initial = initial
        self.revisions = revisions or []
        self.revision_reasons: list[str] = []

    async def plan(self, *_args: Any, **_kwargs: Any) -> AgentPlan:
        return self.initial

    async def revise(self, *_args: Any, reason: str, **_kwargs: Any) -> AgentPlan:
        self.revision_reasons.append(reason)
        if self.revisions:
            return self.revisions.pop(0)
        return AgentPlan(intent="无需修正", answer_strategy="answer_from_observations")

    def fallback_plan(self, *_args: Any, **_kwargs: Any) -> AgentPlan:
        return self.initial


class _FakeRegistry:
    def __init__(self, outputs: dict[str, list[ToolExecution]]) -> None:
        self.outputs = {name: list(values) for name, values in outputs.items()}
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, name: str) -> object:
        return SimpleNamespace(
            clarification="请补充必要信息。",
            definition=SimpleNamespace(input_schema={"required": []}),
        )

    async def execute(self, name: str, params: dict[str, Any], *_args: Any) -> ToolExecution:
        self.calls.append((name, params))
        executions = self.outputs.get(name, [])
        if executions:
            return executions.pop(0)
        return ToolExecution(status="success", output={"result": 1})


def _tool(name: str, arguments: dict[str, Any] | None = None) -> PlannedToolCall:
    return PlannedToolCall(tool_name=name, arguments=arguments or {}, rationale=f"调用 {name}")


def _run(executor: AgentExecutor, task: str = "测试任务"):
    payload = SimpleNamespace(task=task, context_file_ids=[], kb_id=None)
    user = UserPublic(id=1, username="agent-user", email="agent@example.com", display_name="Agent", roles=["user"])
    return asyncio.run(executor.run(payload, SimpleNamespace(), user))


def test_agent_executor_revises_plan_after_failed_tool() -> None:
    planner = _FakePlanner(
        AgentPlan(intent="先失败", plan_steps=[_tool("calculator", {"expression": "2 + abc"})]),
        [AgentPlan(intent="改用正确表达式", plan_steps=[_tool("calculator", {"expression": "2 + 2"})])],
    )
    registry = _FakeRegistry({
        "calculator": [
            ToolExecution(status="failed", error_message="表达式只能包含数字和算术运算符"),
            ToolExecution(status="success", output={"expression": "2 + 2", "result": 4}),
        ],
    })
    executor = AgentExecutor(registry=registry, planner=planner)

    response = _run(executor, "计算 2 + abc")

    assert response.status == "completed"
    assert "4" in response.final_answer
    assert registry.calls == [
        ("calculator", {"expression": "2 + abc"}),
        ("calculator", {"expression": "2 + 2"}),
    ]
    assert any(step.title == "修正规划" for step in response.steps)
    assert planner.revision_reasons == ["calculator 调用失败：表达式只能包含数字和算术运算符"]
    failed_call = next(step for step in response.steps if step.phase == "call" and step.input_json["expression"] == "2 + abc")
    assert failed_call.status == "failed"
    assert failed_call.metadata["latency_ms"] == 0


def test_agent_executor_revises_plan_after_empty_result() -> None:
    planner = _FakePlanner(
        AgentPlan(intent="查文件", plan_steps=[_tool("file_content_search", {"query": "算法", "file_ids": []})]),
        [AgentPlan(intent="改查课程", plan_steps=[_tool("course_lookup", {"query": "算法"})])],
    )
    registry = _FakeRegistry({
        "file_content_search": [ToolExecution(status="success", output={"matches": []})],
        "course_lookup": [ToolExecution(status="success", output={"courses": [
            {"name": "算法设计", "code": "CS201", "teacher": "Li", "credits": 3}
        ], "source": "courses.json"})],
    })
    executor = AgentExecutor(registry=registry, planner=planner)

    response = _run(executor, "查询算法")

    assert response.status == "completed"
    assert [name for name, _ in registry.calls] == ["file_content_search", "course_lookup"]
    assert "算法设计" in response.final_answer
    assert any("未查询到结果" in reason for reason in planner.revision_reasons)


def test_agent_executor_stops_when_tool_call_limit_is_reached() -> None:
    planner = _FakePlanner(
        AgentPlan(intent="太多步骤", plan_steps=[
            _tool("calculator", {"expression": "1 + 1"}),
            _tool("calculator", {"expression": "2 + 2"}),
            _tool("calculator", {"expression": "3 + 3"}),
        ]),
    )
    registry = _FakeRegistry({
        "calculator": [
            ToolExecution(status="success", output={"expression": "1 + 1", "result": 2}),
            ToolExecution(status="success", output={"expression": "2 + 2", "result": 4}),
        ],
    })
    executor = AgentExecutor(registry=registry, planner=planner, max_tool_calls=2)

    response = _run(executor, "执行多个计算")

    assert response.status == "failed"
    assert "工具调用次数超限" in response.final_answer
    assert len(registry.calls) == 2
    assert response.steps[-1].metadata["max_tool_calls"] == 2


def test_agent_executor_previews_plan_risk_without_executing_tools() -> None:
    planner = _FakePlanner(
        AgentPlan(intent="查询数据库", plan_steps=[
            _tool("database_query", {"table": "files"}),
        ]),
    )
    registry = _FakeRegistry({"database_query": [ToolExecution(status="success", output={"rows": []})]})
    executor = AgentExecutor(registry=registry, planner=planner)
    payload = SimpleNamespace(task="数据库查询文件", context_file_ids=[], kb_id=None)
    user = UserPublic(id=1, username="agent-user", email="agent@example.com", display_name="Agent", roles=["user"])

    preview = asyncio.run(executor.preview_plan(payload, user))

    assert preview.risk_level == "high"
    assert preview.requires_confirmation is True
    assert preview.steps[0].tool_name == "database_query"
    assert registry.calls == []
