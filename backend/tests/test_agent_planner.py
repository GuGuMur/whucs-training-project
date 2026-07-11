from __future__ import annotations

import asyncio

from app.services.agent_planner import AgentPlanner, ToolCallingLLM
from app.services.tool_registry import ToolRegistry


class _FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> object:
        self.prompts.append(prompt)
        return type("_Response", (), {"content": self.content})()


class _UnavailableLLM:
    def available(self) -> bool:
        return False

    async def complete(self, _prompt: str) -> str | None:
        raise AssertionError("unavailable LLM should not be called")


def _plan(task: str, llm_content: str | None = None, *, context_file_ids: list[str] | None = None):
    planner = AgentPlanner(
        registry=ToolRegistry(),
        tool_llm=ToolCallingLLM(_FakeLLM(llm_content)) if llm_content is not None else _UnavailableLLM(),
    )
    return asyncio.run(planner.plan(task, context_file_ids or [], None, {}))


def test_agent_planner_falls_back_without_llm() -> None:
    plan = _plan("计算 2 + 3 并查询算法课程信息")

    assert plan.intent == "计算并查询课程"
    assert [(step.tool_name, step.arguments) for step in plan.plan_steps] == [
        ("calculator", {"expression": "2 + 3"}),
        ("course_lookup", {"query": "算法"}),
    ]


def test_agent_planner_parses_valid_llm_json() -> None:
    plan = _plan(
        "在文件内容中查询 alpha",
        """
        {
          "intent": "搜索文件内容",
          "missing_fields": [],
          "plan_steps": [
            {
              "tool_name": "file_content_search",
              "arguments": {"query": "alpha"},
              "rationale": "查找相关文件片段"
            }
          ],
          "answer_strategy": "引用文件片段回答"
        }
        """,
        context_file_ids=["file-1"],
    )

    assert plan.intent == "搜索文件内容"
    assert plan.plan_steps[0].tool_name == "file_content_search"
    assert plan.plan_steps[0].arguments == {"query": "alpha", "file_ids": ["file-1"], "kb_id": None}
    assert "chain_of_thought" not in plan.model_dump()


def test_agent_planner_repairs_fenced_json() -> None:
    plan = _plan(
        "计算 (2 + 3) * 4",
        """
        这是计划：
        ```json
        {"intent":"计算","missing_fields":[],"plan_steps":[{"tool_name":"calculator","arguments":{"expression":"(2 + 3) * 4"}}],"answer_strategy":"返回计算结果"}
        ```
        """,
    )

    assert plan.plan_steps[0].tool_name == "calculator"
    assert plan.plan_steps[0].arguments["expression"] == "(2 + 3) * 4"


def test_agent_planner_invalid_json_uses_fallback() -> None:
    plan = _plan("查询算法课程信息", "不是 JSON")

    assert plan.plan_steps[0].tool_name == "course_lookup"
    assert plan.plan_steps[0].arguments == {"query": "算法"}


def test_agent_planner_rejects_unknown_llm_tool() -> None:
    plan = _plan(
        "计算 1 + 1",
        '{"intent":"hack","missing_fields":[],"plan_steps":[{"tool_name":"shell","arguments":{"cmd":"rm -rf /"}}],"answer_strategy":"run"}',
    )

    assert plan.plan_steps[0].tool_name == "calculator"
    assert "cmd" not in plan.plan_steps[0].arguments


def test_agent_planner_missing_course_query_requests_clarification() -> None:
    plan = _plan("查询课程信息")

    assert plan.missing_fields == ["query"]
    assert plan.plan_steps[0].tool_name == "course_lookup"
    assert plan.plan_steps[0].arguments == {"query": ""}


def test_agent_planner_fallback_selects_phase34_tools() -> None:
    file_plan = _plan("查询失败文件列表")
    db_plan = _plan("数据库查询知识库")
    weather_plan = _plan("查询武汉天气")
    rag_plan = _plan("查询知识库 讲解课程资料")

    assert file_plan.plan_steps[0].tool_name == "file_metadata_query"
    assert file_plan.plan_steps[0].arguments["parse_status"] == "failed"
    assert db_plan.plan_steps[0].tool_name == "database_query"
    assert db_plan.plan_steps[0].arguments["table"] == "knowledge_bases"
    assert weather_plan.plan_steps[0].tool_name == "weather_lookup"
    assert weather_plan.plan_steps[0].arguments["location"] == "武汉"
    assert rag_plan.plan_steps[0].tool_name == "rag_query"
