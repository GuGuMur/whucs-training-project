from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from app.domain.schemas import FileItem, KnowledgeBasePublic, QAResponse, UserPublic
from app.services.agent_executor import AgentExecutor
from app.services.agent_planner import AgentPlanner
from app.services.tool_registry import ToolRegistry


class _UnavailableLLM:
    def available(self) -> bool:
        return False

    async def complete(self, _prompt: str) -> str | None:
        raise AssertionError("evaluation must use deterministic fallback planning")


class _Files:
    def __init__(self, files: dict[str, Any]) -> None:
        self._files = files

    async def get_by_id(self, file_id: str) -> Any | None:
        return self._files.get(file_id)


class _EvaluationWorkspace:
    def __init__(self) -> None:
        now = datetime(2026, 7, 11, tzinfo=UTC)
        self.audit_events: list[dict[str, Any]] = []
        self._raw_files = {
            "file-notes": SimpleNamespace(id="file-notes", name="eval-notes.txt"),
            "file-csv": SimpleNamespace(id="file-csv", name="scores.csv"),
        }
        self._contents = {
            "file-notes": b"beta launch checklist\nalpha risk register\ncourse project notes",
            "file-csv": b"name,score\nalice,80\nbob,95\n",
        }
        self._files = _Files(self._raw_files)
        self.files = [
            FileItem(
                id="file-notes",
                name="eval-notes.txt",
                folder_id="personal-root-1",
                type="txt",
                size=len(self._contents["file-notes"]),
                sha256="notes",
                parse_status="indexed",
                tags=["eval", "project"],
                updated_at=now,
                permission_scope="personal",
                knowledge_base_ids=["kb-1"],
            ),
            FileItem(
                id="file-csv",
                name="scores.csv",
                folder_id="personal-root-1",
                type="csv",
                size=len(self._contents["file-csv"]),
                sha256="csv",
                parse_status="indexed",
                tags=["eval", "data"],
                updated_at=now,
                permission_scope="personal",
                knowledge_base_ids=[],
            ),
            FileItem(
                id="file-failed",
                name="broken.pdf",
                folder_id="personal-root-1",
                type="pdf",
                size=0,
                sha256="failed",
                parse_status="failed",
                tags=["eval"],
                updated_at=now,
                permission_scope="personal",
                knowledge_base_ids=[],
            ),
        ]
        self.kbs = [
            KnowledgeBasePublic(
                id="kb-1",
                name="课程知识库",
                description="课程资料与项目说明",
                status="active",
                document_count=1,
                chunk_count=3,
                updated_at=now,
                scope_type="personal",
                tags=["course"],
            )
        ]

    async def list_files(self, _user: UserPublic) -> list[FileItem]:
        return self.files

    async def list_knowledge_bases(self, _user: UserPublic) -> list[KnowledgeBasePublic]:
        return self.kbs

    async def answer_question(self, payload: Any, _user: UserPublic) -> QAResponse:
        return QAResponse(
            conversation_id="conv-eval",
            message_id="msg-eval",
            answer=f"知识库回答：{payload.question}",
            citations=[],
        )

    async def _ensure_kb_access(self, kb_id: str, _user: UserPublic) -> None:
        if kb_id != "kb-1":
            raise PermissionError(f"知识库不存在或无权访问：{kb_id}")

    async def record_agent_tool_execution(self, user: UserPublic, tool_name: str, execution: Any) -> None:
        self.audit_events.append({
            "user": user.username,
            "tool": tool_name,
            "status": execution.status,
            "latency_ms": execution.latency_ms,
        })

    def read_file_content_for_tool(self, file: Any) -> bytes | None:
        return self._contents.get(file.id)


@dataclass(frozen=True)
class _EvalCase:
    name: str
    task: str
    expected_status: str
    expected_tools: list[str]
    context_file_ids: list[str] = field(default_factory=list)
    kb_id: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    expected_args: dict[str, Any] = field(default_factory=dict)
    require_answer_contains: str | None = None


def _user() -> UserPublic:
    return UserPublic(id=1, username="eval-user", email="eval@example.com", display_name="Eval", roles=["user"])


def _executor() -> AgentExecutor:
    registry = ToolRegistry()
    planner = AgentPlanner(registry=registry, tool_llm=_UnavailableLLM())
    return AgentExecutor(registry=registry, planner=planner)


def _run_case(case: _EvalCase):
    payload = SimpleNamespace(task=case.task, context_file_ids=case.context_file_ids, kb_id=case.kb_id)
    return asyncio.run(_executor().run(payload, _EvaluationWorkspace(), _user(), continuation_inputs=case.inputs))


def test_agent_tool_flow_evaluation_covers_25_acceptance_cases(monkeypatch) -> None:
    monkeypatch.delenv("WEATHER_API_URL", raising=False)
    cases = [
        _EvalCase("direct", "解释什么是机器学习", "completed", [], require_answer_contains="可直接回答"),
        _EvalCase("calc_add", "计算 2 + 3", "completed", ["calculator"], expected_args={"expression": "2 + 3"}),
        _EvalCase("calc_parentheses", "计算 (2 + 3) * 4", "completed", ["calculator"]),
        _EvalCase("calc_invalid", "计算 2 + abc", "failed", ["calculator"]),
        _EvalCase("course_success", "查询算法课程信息", "completed", ["course_lookup"], expected_args={"query": "算法"}),
        _EvalCase("course_empty", "查询不存在课程信息", "completed", ["course_lookup"]),
        _EvalCase("course_clarify", "查询课程信息", "needs_clarification", ["course_lookup"]),
        _EvalCase("file_search_hit", "在文件内容中查询 beta", "completed", ["file_content_search"], context_file_ids=["file-notes"]),
        _EvalCase("file_search_empty", "在文件内容中查询 gamma", "completed", ["file_content_search"], context_file_ids=["file-notes"]),
        _EvalCase("file_search_denied", "在文件内容中查询 secret", "failed", ["file_content_search"], context_file_ids=["file-secret"]),
        _EvalCase("file_metadata_failed", "查询失败文件列表", "completed", ["file_metadata_query"]),
        _EvalCase("file_metadata_tags", "查询 eval 文件列表", "completed", ["file_metadata_query"]),
        _EvalCase("csv_analysis", "分析csv数据", "completed", ["python_data"], context_file_ids=["file-csv"]),
        _EvalCase("csv_denied", "分析csv数据", "failed", ["python_data"], context_file_ids=["file-secret"]),
        _EvalCase("rag_success", "查询知识库 讲解课程资料", "completed", ["rag_query"], kb_id="kb-1"),
        _EvalCase("rag_missing_kb", "查询知识库 讲解课程资料", "needs_clarification", ["rag_query"]),
        _EvalCase("rag_denied", "查询知识库 讲解课程资料", "failed", ["rag_query"], kb_id="kb-secret"),
        _EvalCase("db_files", "数据库查询文件 beta", "completed", ["database_query"]),
        _EvalCase("db_kbs", "数据库查询知识库 课程", "completed", ["database_query"]),
        _EvalCase("weather_unconfigured", "查询武汉天气", "failed", ["weather_lookup"]),
        _EvalCase("multi_calc_course", "计算 2 + 2 并查询算法课程信息", "completed", ["calculator", "course_lookup"]),
        _EvalCase("multi_file_csv", "在文件内容中查询 beta 并分析csv数据", "completed", ["file_content_search", "python_data"], context_file_ids=["file-notes", "file-csv"], inputs={"file_id": "file-csv"}),
        _EvalCase("multi_calc_file", "计算 5 * 5 并在文件内容中查询 alpha", "completed", ["calculator", "file_content_search"], context_file_ids=["file-notes"]),
        _EvalCase("multi_turn_direct", "继续补充考试时间", "completed", [], inputs={"_history": [{"role": "user", "content": "之前查询算法课程"}]}, require_answer_contains="前文要点"),
        _EvalCase("invalid_unknown_db_table_guard", "数据库查询用户表", "needs_clarification", ["database_query"]),
    ]

    results = []
    for case in cases:
        response = _run_case(case)
        call_steps = [step for step in response.steps if step.phase == "call"]
        called_tools = [step.tool_name for step in call_steps]
        args_ok = all(
            any(step.input_json.get(key) == value for step in call_steps)
            for key, value in case.expected_args.items()
        )
        latency_values = [int(step.metadata.get("latency_ms", -1)) for step in call_steps]
        results.append({
            "name": case.name,
            "status": response.status,
            "expected_status": case.expected_status,
            "tools": called_tools,
            "expected_tools": case.expected_tools,
            "args_ok": args_ok,
            "latency_values": latency_values,
            "answer": response.final_answer,
        })

    completion_matches = sum(1 for item in results if item["status"] == item["expected_status"])
    tool_matches = sum(1 for item in results if item["tools"] == item["expected_tools"])
    arg_matches = sum(1 for item in results if item["args_ok"])
    latency_covered = sum(
        1 for item in results
        if not item["tools"] or all(value >= 0 for value in item["latency_values"])
    )
    grounded_answers = sum(
        1 for case, item in zip(cases, results, strict=True)
        if case.require_answer_contains is None or case.require_answer_contains in item["answer"]
    )

    total = len(cases)
    assert total >= 25
    assert completion_matches / total >= 0.85, results
    assert tool_matches / total >= 0.85, results
    assert arg_matches / total >= 0.85, results
    assert latency_covered / total >= 0.85, results
    assert grounded_answers / total >= 0.85, results
