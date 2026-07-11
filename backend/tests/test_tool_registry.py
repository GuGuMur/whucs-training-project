from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from app.domain.schemas import FileItem, KnowledgeBasePublic, QAResponse, UserPublic
from app.services import tool_registry
from app.services.agent_executor import AgentExecutor
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
        self.documents = [
            SimpleNamespace(
                id="doc-1",
                kb_id="kb-1",
                file_id="file-1",
                file_name="rag-transformer-notes.md",
                index_status="indexed",
                chunk_count=3,
                summary="Retrieval augmented generation, transformers, semantic search and evaluation",
                char_count=1200,
                token_count=200,
                updated_at=datetime(2026, 7, 10, tzinfo=UTC),
            )
        ]
        self.created_markdown: dict[str, Any] | None = None

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

    async def list_knowledge_documents(self, kb_id: str, _user: UserPublic) -> list[Any]:
        return [doc for doc in self.documents if doc.kb_id == kb_id]

    async def list_knowledge_document_profiles(self, kb_id: str, _user: UserPublic) -> list[dict[str, Any]]:
        return [
            {
                "id": doc.id,
                "file_id": doc.file_id,
                "file_name": doc.file_name,
                "summary": doc.summary,
                "keywords": ["retrieval augmented generation", "transformers"],
                "outline": ["semantic search evaluation"],
                "content_preview": "RAG systems combine dense retrieval, reranking and language model generation.",
            }
            for doc in self.documents
            if doc.kb_id == kb_id
        ]

    async def create_markdown_knowledge_document(
        self,
        kb_id: str,
        filename: str,
        markdown: str,
        tags: list[str],
        _user: UserPublic,
    ) -> Any:
        self.created_markdown = {
            "kb_id": kb_id,
            "filename": filename,
            "markdown": markdown,
            "tags": tags,
        }
        return SimpleNamespace(
            id="doc-report",
            kb_id=kb_id,
            file_id="file-report",
            file_name=filename,
            index_status="indexed",
            chunk_count=2,
            summary="arXiv report",
            char_count=len(markdown),
            token_count=len(markdown.split()),
            updated_at=datetime(2026, 7, 11, tzinfo=UTC),
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
    assert {"kb_interest_extract", "arxiv_search", "arxiv_markdown_render", "knowledge_markdown_write"}.issubset(names)


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


def test_arxiv_tools_extract_search_render_and_write(monkeypatch) -> None:
    workspace = _FakeWorkspace()

    def fake_fetch(interests: list[str], *, days: int, max_results: int) -> list[dict[str, Any]]:
        assert days == 3
        assert max_results == 2
        assert "retrieval augmented generation" in interests or "transformers" in interests
        return [
            {
                "id": "http://arxiv.org/abs/2607.00001v1",
                "title": "Fresh RAG Evaluation",
                "abstract": "A recent paper about retrieval augmented generation evaluation.",
                "authors": ["A. Researcher"],
                "published": "2026-07-10T00:00:00Z",
                "updated": "2026-07-10T00:00:00Z",
                "link": "http://arxiv.org/abs/2607.00001v1",
                "pdf_url": "http://arxiv.org/pdf/2607.00001v1",
                "categories": ["cs.CL"],
            }
        ]

    monkeypatch.setattr(tool_registry, "_fetch_arxiv_papers", fake_fetch)

    interests = _run_tool("kb_interest_extract", {"kb_id": "kb-1"}, workspace)
    search = _run_tool("arxiv_search", {"interests": interests.output["interests"], "days": 3, "max_results": 2}, workspace)
    render = _run_tool(
        "arxiv_markdown_render",
        {"interests": interests.output["interests"], "papers": search.output["papers"], "days": 3},
        workspace,
    )
    result = _run_tool("knowledge_markdown_write", {"kb_id": "kb-1", "markdown": render.output["markdown"]}, workspace)

    assert result.status == "success"
    assert result.output["document_id"] == "doc-report"
    assert result.output["file_id"] == "file-report"
    assert search.output["papers"][0]["title"] == "Fresh RAG Evaluation"
    assert render.output["paper_count"] == 1
    assert workspace.created_markdown is not None
    assert workspace.created_markdown["kb_id"] == "kb-1"
    assert "# arXiv 近期论文推荐" in workspace.created_markdown["markdown"]
    assert "Fresh RAG Evaluation" in workspace.created_markdown["markdown"]


def test_agent_runs_decoupled_arxiv_interest_tool_chain(monkeypatch) -> None:
    workspace = _FakeWorkspace()

    def fake_fetch(_interests: list[str], *, days: int, max_results: int) -> list[dict[str, Any]]:
        assert days == 3
        assert max_results == 2
        return [
            {
                "id": "http://arxiv.org/abs/2607.00001v1",
                "title": "Fresh RAG Evaluation",
                "abstract": "A recent paper about retrieval augmented generation evaluation.",
                "authors": ["A. Researcher"],
                "published": "2026-07-10T00:00:00Z",
                "updated": "2026-07-10T00:00:00Z",
                "link": "http://arxiv.org/abs/2607.00001v1",
                "pdf_url": "http://arxiv.org/pdf/2607.00001v1",
                "categories": ["cs.CL"],
            }
        ]

    monkeypatch.setattr(tool_registry, "_fetch_arxiv_papers", fake_fetch)
    payload = SimpleNamespace(
        task="读取知识库内文档，提取用户兴趣，然后从 arxiv 获取最近 3 天的 2 篇相关论文，整理 markdown 存回知识库",
        kb_id="kb-1",
        context_file_ids=[],
    )
    executor = AgentExecutor(registry=ToolRegistry())

    response = asyncio.run(executor.run(payload, workspace, _user()))

    assert response.status == "completed"
    assert [step.tool_name for step in response.steps if step.phase == "call"] == [
        "kb_interest_extract",
        "arxiv_search",
        "arxiv_markdown_render",
        "knowledge_markdown_write",
    ]
    assert workspace.created_markdown is not None
    assert "Fresh RAG Evaluation" in workspace.created_markdown["markdown"]
    assert "doc-report" in response.final_answer


def test_weather_lookup_requires_real_provider_configuration(monkeypatch) -> None:
    monkeypatch.delenv("QWEATHER_HOST", raising=False)
    monkeypatch.delenv("QWEATHER_KEY", raising=False)

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
    monkeypatch.delenv("QWEATHER_HOST", raising=False)

    issues = ToolRegistry().validate_configuration()

    assert any(issue["code"] == "QWEATHER_HOST_MISSING" for issue in issues)
