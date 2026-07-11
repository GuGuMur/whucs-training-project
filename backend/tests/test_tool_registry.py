from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from app.domain.schemas import FileItem, KnowledgeBasePublic, QAResponse, UserPublic
from app.services.tool_registry import ToolRegistry


class _FakeWorkspace:
    def __init__(self) -> None:
        self.audit_events: list[dict[str, object]] = []
        self.files = [
            FileItem(
                id="file-1",
                name="notes.md",
                folder_id="personal-root-1",
                type="md",
                size=128,
                sha256="abc",
                parse_status="indexed",
                tags=["rag", "course"],
                updated_at=datetime(2026, 7, 10, tzinfo=UTC),
                permission_scope="personal",
                knowledge_base_ids=["kb-1"],
            ),
            FileItem(
                id="file-2",
                name="scores.csv",
                folder_id="personal-root-1",
                type="csv",
                size=64,
                sha256="def",
                parse_status="failed",
                tags=["data"],
                updated_at=datetime(2026, 7, 9, tzinfo=UTC),
                permission_scope="personal",
                knowledge_base_ids=[],
            ),
        ]
        self.kbs = [
            KnowledgeBasePublic(
                id="kb-1",
                name="课程知识库",
                description="课程资料",
                status="active",
                document_count=1,
                chunk_count=3,
                updated_at=datetime(2026, 7, 10, tzinfo=UTC),
            )
        ]

    async def list_files(self, _user: UserPublic) -> list[FileItem]:
        return self.files

    async def list_knowledge_bases(self, _user: UserPublic) -> list[KnowledgeBasePublic]:
        return self.kbs

    async def answer_question(self, payload: Any, _user: UserPublic) -> QAResponse:
        return QAResponse(
            conversation_id="conv-1",
            message_id="msg-1",
            answer=f"回答：{payload.question}",
            citations=[],
        )

    async def record_agent_tool_execution(self, user: UserPublic, tool_name: str, execution: Any) -> None:
        self.audit_events.append({
            "user": user.username,
            "tool": tool_name,
            "status": execution.status,
            "latency_ms": execution.latency_ms,
            "error": execution.error_message,
        })


def _user() -> UserPublic:
    return UserPublic(id=1, username="owner", email="owner@example.com", display_name="Owner", roles=["user"])


def _run_tool(name: str, params: dict[str, Any], workspace: _FakeWorkspace | None = None):
    registry = ToolRegistry()
    return asyncio.run(registry.execute(name, params, workspace or _FakeWorkspace(), _user()))


def test_tool_catalog_contains_phase34_tools() -> None:
    names = {definition.name for definition in ToolRegistry().definitions()}

    assert {"rag_query", "file_metadata_query", "database_query", "weather_lookup"}.issubset(names)


def test_file_metadata_query_filters_user_visible_files() -> None:
    workspace = _FakeWorkspace()
    result = _run_tool("file_metadata_query", {"query": "score", "parse_status": "failed"}, workspace)

    assert result.status == "success"
    assert result.output["total"] == 1
    assert result.output["files"][0]["name"] == "scores.csv"
    assert result.output["files"][0]["parse_status"] == "failed"
    assert workspace.audit_events[0]["tool"] == "file_metadata_query"
    assert workspace.audit_events[0]["status"] == "success"
    assert isinstance(workspace.audit_events[0]["latency_ms"], int)


def test_database_query_reads_whitelisted_tables_only() -> None:
    result = _run_tool("database_query", {"table": "knowledge_bases", "limit": 5})

    assert result.status == "success"
    assert result.output["table"] == "knowledge_bases"
    assert result.output["rows"][0]["name"] == "课程知识库"

    denied = _run_tool("database_query", {"table": "users"})
    assert denied.status == "failed"
    assert "不允许查询的数据表" in denied.error_message


def test_rag_query_delegates_to_workspace_rag() -> None:
    result = _run_tool("rag_query", {"kb_id": "kb-1", "question": "讲解课程资料"})

    assert result.status == "success"
    assert result.output["answer"] == "回答：讲解课程资料"
    assert result.output["conversation_id"] == "conv-1"


def test_weather_lookup_requires_real_provider_configuration(monkeypatch) -> None:
    monkeypatch.delenv("WEATHER_API_URL", raising=False)
    monkeypatch.delenv("WEATHER_API_KEY", raising=False)

    result = _run_tool("weather_lookup", {"location": "武汉"})

    assert result.status == "failed"
    assert "天气工具未配置" in result.error_message


def test_tool_registry_rejects_inaccessible_file_before_tool_execution() -> None:
    workspace = _FakeWorkspace()

    result = _run_tool("file_content_search", {"query": "secret", "file_ids": ["file-secret"]}, workspace)

    assert result.status == "failed"
    assert "无权访问" in result.error_message
    assert workspace.audit_events[0]["tool"] == "file_content_search"
    assert workspace.audit_events[0]["status"] == "failed"


def test_tool_registry_reports_configuration_issues(monkeypatch) -> None:
    monkeypatch.delenv("WEATHER_API_URL", raising=False)

    issues = ToolRegistry().validate_configuration()

    assert any(issue["code"] == "WEATHER_API_URL_MISSING" for issue in issues)
