from __future__ import annotations

import asyncio
import ast
import csv
import difflib
import io
import json
import logging
import operator
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Awaitable, Callable

from app.domain.schemas import QARequest, ToolDefinition, UserPublic


_COURSE_CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "courses.json"
logger = logging.getLogger(__name__)


ToolHandler = Callable[[dict[str, Any], Any, UserPublic], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ToolSpec:
    definition: ToolDefinition
    handler: ToolHandler
    clarification: str
    allowed_roles: tuple[str, ...] = ("user", "admin")


@dataclass
class ToolExecution:
    status: str
    output: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    clarification: str | None = None
    latency_ms: int = 0


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {
            "calculator": ToolSpec(
                definition=ToolDefinition(
                    id="tool-calculator",
                    name="calculator",
                    version="1.0.0",
                    category="计算",
                    description="安全计算简单算术表达式。",
                    input_schema={
                        "type": "object",
                        "required": ["expression"],
                        "properties": {"expression": {"type": "string"}},
                    },
                    output_schema={
                        "type": "object",
                        "properties": {"result": {"type": "number"}, "expression": {"type": "string"}},
                    },
                ),
                handler=self._calculator,
                clarification="请补充要计算的算术表达式。",
            ),
            "course_lookup": ToolSpec(
                definition=ToolDefinition(
                    id="tool-course-lookup",
                    name="course_lookup",
                    version="1.0.0",
                    category="课程",
                    description="按课程名称或关键词查询课程信息。",
                    input_schema={
                        "type": "object",
                        "required": ["query"],
                        "properties": {"query": {"type": "string"}},
                    },
                    output_schema={
                        "type": "object",
                        "properties": {"courses": {"type": "array"}},
                    },
                ),
                handler=self._course_lookup,
                clarification="请补充要查询的课程名称。",
            ),
            "file_content_search": ToolSpec(
                definition=ToolDefinition(
                    id="tool-file-content-search",
                    name="file_content_search",
                    version="1.0.0",
                    category="文件",
                    description="在用户可访问的文件内容中搜索关键词。",
                    input_schema={
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {"type": "string"},
                            "file_ids": {"type": "array", "items": {"type": "string"}},
                            "kb_id": {"type": "string"},
                        },
                    },
                    output_schema={
                        "type": "object",
                        "properties": {"matches": {"type": "array"}},
                    },
                ),
                handler=self._file_content_search,
                clarification="请补充要在文件中查询的关键词。",
            ),
            "file_compare": ToolSpec(
                definition=ToolDefinition(
                    id="tool-file-compare",
                    name="file_compare",
                    version="2.0.0",
                    category="文件",
                    description="逐行比对两个可访问文本文件并生成结构化 Markdown 差异报告。",
                    input_schema={
                        "type": "object",
                        "required": ["file_a", "file_b"],
                        "properties": {
                            "file_a": {"type": "string"},
                            "file_b": {"type": "string"},
                            "context_lines": {"type": "integer", "minimum": 0, "maximum": 10},
                        },
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "report": {"type": "string"},
                            "diff": {"type": "string"},
                            "summary": {"type": "object"},
                            "file_a": {"type": "object"},
                            "file_b": {"type": "object"},
                        },
                    },
                ),
                handler=self._file_compare,
                clarification="请选择两个需要比对的文本文件。",
            ),
            "python_data": ToolSpec(
                definition=ToolDefinition(
                    id="tool-python-data",
                    name="python_data",
                    version="1.0.0",
                    category="数据",
                    description="读取 CSV 文本文件并返回行数、列名和数值列统计。",
                    input_schema={
                        "type": "object",
                        "required": ["file_id"],
                        "properties": {"file_id": {"type": "string"}},
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "row_count": {"type": "integer"},
                            "columns": {"type": "array"},
                            "numeric_summary": {"type": "object"},
                        },
                    },
                ),
                handler=self._python_data,
                clarification="请补充要分析的 CSV 文件。",
            ),
            "rag_query": ToolSpec(
                definition=ToolDefinition(
                    id="tool-rag-query",
                    name="rag_query",
                    version="1.0.0",
                    category="知识库",
                    description="查询用户可访问的知识库并返回带引用的 RAG 回答。",
                    input_schema={
                        "type": "object",
                        "required": ["kb_id", "question"],
                        "properties": {
                            "kb_id": {"type": "string"},
                            "question": {"type": "string"},
                            "top_k": {"type": "integer", "minimum": 1, "maximum": 30},
                        },
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "answer": {"type": "string"},
                            "citations": {"type": "array"},
                            "error_code": {"type": "string"},
                        },
                    },
                ),
                handler=self._rag_query,
                clarification="请补充知识库 ID 和要提问的问题。",
            ),
            "file_metadata_query": ToolSpec(
                definition=ToolDefinition(
                    id="tool-file-metadata-query",
                    name="file_metadata_query",
                    version="1.0.0",
                    category="文件",
                    description="按名称、标签、类型或解析状态查询用户可访问文件的元数据。",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "tag": {"type": "string"},
                            "type": {"type": "string"},
                            "parse_status": {"type": "string"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                        },
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "total": {"type": "integer"},
                            "files": {"type": "array"},
                        },
                    },
                ),
                handler=self._file_metadata_query,
                clarification="请补充要查询的文件条件。",
            ),
            "database_query": ToolSpec(
                definition=ToolDefinition(
                    id="tool-database-query",
                    name="database_query",
                    version="1.0.0",
                    category="数据库",
                    description="查询受限只读系统数据表，不支持任意 SQL 或写操作。",
                    input_schema={
                        "type": "object",
                        "required": ["table"],
                        "properties": {
                            "table": {"type": "string", "enum": ["files", "knowledge_bases"]},
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                        },
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "table": {"type": "string"},
                            "columns": {"type": "array"},
                            "rows": {"type": "array"},
                        },
                    },
                ),
                handler=self._database_query,
                clarification="请补充要查询的受限数据表名称。",
            ),
            "weather_lookup": ToolSpec(
                definition=ToolDefinition(
                    id="tool-weather-lookup",
                    name="weather_lookup",
                    version="1.0.0",
                    category="外部服务",
                    description="通过已配置的真实天气 API 查询地点天气；未配置时返回明确错误。",
                    input_schema={
                        "type": "object",
                        "required": ["location"],
                        "properties": {"location": {"type": "string"}},
                    },
                    output_schema={
                        "type": "object",
                        "properties": {"location": {"type": "string"}, "provider_response": {"type": "object"}},
                    },
                ),
                handler=self._weather_lookup,
                clarification="请补充要查询天气的地点。",
            ),
            "kb_interest_extract": ToolSpec(
                definition=ToolDefinition(
                    id="tool-kb-interest-extract",
                    name="kb_interest_extract",
                    version="1.0.0",
                    category="知识库",
                    description="读取知识库文档画像，提取用户研究兴趣关键词。",
                    input_schema={
                        "type": "object",
                        "required": ["kb_id"],
                        "properties": {
                            "kb_id": {"type": "string"},
                            "query": {"type": "string"},
                            "max_terms": {"type": "integer", "minimum": 1, "maximum": 20},
                        },
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string"},
                            "interests": {"type": "array"},
                            "documents": {"type": "array"},
                        },
                    },
                ),
                handler=self._kb_interest_extract,
                clarification="请补充要读取的知识库 ID。",
            ),
            "arxiv_search": ToolSpec(
                definition=ToolDefinition(
                    id="tool-arxiv-search",
                    name="arxiv_search",
                    version="1.0.0",
                    category="科研",
                    description="根据兴趣关键词从 arXiv 获取近几天的相关论文。",
                    input_schema={
                        "type": "object",
                        "required": ["interests"],
                        "properties": {
                            "interests": {"type": "array", "items": {"type": "string"}},
                            "days": {"type": "integer", "minimum": 1, "maximum": 30},
                            "max_results": {"type": "integer", "minimum": 1, "maximum": 20},
                        },
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "interests": {"type": "array"},
                            "papers": {"type": "array"},
                            "days": {"type": "integer"},
                            "max_results": {"type": "integer"},
                        },
                    },
                ),
                handler=self._arxiv_search,
                clarification="请补充用于检索 arXiv 的兴趣关键词。",
            ),
            "arxiv_markdown_render": ToolSpec(
                definition=ToolDefinition(
                    id="tool-arxiv-markdown-render",
                    name="arxiv_markdown_render",
                    version="1.0.0",
                    category="科研",
                    description="将 arXiv 论文列表整理成 Markdown 报告。",
                    input_schema={
                        "type": "object",
                        "required": ["interests", "papers"],
                        "properties": {
                            "interests": {"type": "array", "items": {"type": "string"}},
                            "papers": {"type": "array"},
                            "days": {"type": "integer", "minimum": 1, "maximum": 30},
                        },
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "markdown": {"type": "string"},
                            "paper_count": {"type": "integer"},
                            "interests": {"type": "array"},
                        },
                    },
                ),
                handler=self._arxiv_markdown_render,
                clarification="请补充兴趣关键词和论文列表。",
            ),
            "knowledge_markdown_write": ToolSpec(
                definition=ToolDefinition(
                    id="tool-knowledge-markdown-write",
                    name="knowledge_markdown_write",
                    version="1.0.0",
                    category="知识库",
                    description="把 Markdown 内容保存为文件并写入指定知识库。",
                    input_schema={
                        "type": "object",
                        "required": ["kb_id", "markdown"],
                        "properties": {
                            "kb_id": {"type": "string"},
                            "markdown": {"type": "string"},
                            "filename": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "kb_id": {"type": "string"},
                            "document_id": {"type": "string"},
                            "file_id": {"type": "string"},
                            "file_name": {"type": "string"},
                            "markdown": {"type": "string"},
                        },
                    },
                ),
                handler=self._knowledge_markdown_write,
                clarification="请补充知识库 ID 和 Markdown 内容。",
            ),
        }

    def definitions(self) -> list[ToolDefinition]:
        return [spec.definition for spec in self._tools.values()]

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    async def execute(self, name: str, params: dict[str, Any], workspace: Any, user: UserPublic) -> ToolExecution:
        started_at = time.monotonic()
        spec = self.get(name)
        if spec is None:
            execution = ToolExecution(status="failed", error_message=f"未知工具：{name}")
            await self._record_execution(workspace, user, name, execution, started_at)
            return self._with_latency(name, execution, started_at)
        try:
            self._ensure_role_allowed(spec, user)
            missing = self._missing_required(spec.definition, params)
            if missing:
                execution = ToolExecution(status="needs_clarification", clarification=spec.clarification)
                await self._record_execution(workspace, user, name, execution, started_at)
                return self._with_latency(name, execution, started_at)
            await self._preflight_access(name, params, workspace, user)
            output = await spec.handler(params, workspace, user)
            execution = ToolExecution(status="success", output=output)
        except Exception as exc:
            execution = ToolExecution(status="failed", error_message=str(exc))
        await self._record_execution(workspace, user, name, execution, started_at)
        return self._with_latency(name, execution, started_at)

    def validate_configuration(self) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        if "weather_lookup" in self._tools and not os.environ.get("QWEATHER_HOST", "").strip():
            issues.append({
                "tool": "weather_lookup",
                "code": "QWEATHER_HOST_MISSING",
                "message": "天气工具未配置 QWEATHER_HOST。",
            })
        if not _COURSE_CATALOG_PATH.exists():
            issues.append({
                "tool": "course_lookup",
                "code": "COURSE_CATALOG_MISSING",
                "message": f"课程目录不存在：{_COURSE_CATALOG_PATH}",
            })
        return issues

    def _missing_required(self, definition: ToolDefinition, params: dict[str, Any]) -> list[str]:
        missing: list[str] = []
        for key in definition.input_schema.get("required", []):
            value = params.get(key)
            if value is None or value == "" or value == []:
                missing.append(str(key))
        return missing

    def _ensure_role_allowed(self, spec: ToolSpec, user: UserPublic) -> None:
        roles = set(user.roles or ["user"])
        if not roles.intersection(spec.allowed_roles):
            raise PermissionError(f"当前角色无权调用工具：{spec.definition.name}")

    async def _preflight_access(self, name: str, params: dict[str, Any], workspace: Any, user: UserPublic) -> None:
        if name in {"file_content_search", "python_data", "file_compare"}:
            visible_files = await workspace.list_files(user)
            visible_ids = {str(getattr(file, "id", "")) for file in visible_files}
            if name == "file_content_search":
                requested_ids = [str(item) for item in params.get("file_ids", [])]
            elif name == "file_compare":
                requested_ids = [str(params.get("file_a", "")), str(params.get("file_b", ""))]
            else:
                requested_ids = [str(params.get("file_id", ""))]
            requested_ids = [item for item in requested_ids if item]
            denied = [file_id for file_id in requested_ids if file_id not in visible_ids]
            if denied:
                raise PermissionError(f"文件不存在或无权访问：{', '.join(denied)}")
        elif name in {"rag_query", "kb_interest_extract", "knowledge_markdown_write"} and hasattr(workspace, "_ensure_kb_access"):
            await workspace._ensure_kb_access(str(params.get("kb_id", "")), user)

    async def _record_execution(
        self,
        workspace: Any,
        user: UserPublic,
        tool_name: str,
        execution: ToolExecution,
        started_at: float,
    ) -> None:
        execution.latency_ms = self._elapsed_ms(started_at)
        if hasattr(workspace, "record_agent_tool_execution"):
            await workspace.record_agent_tool_execution(user, tool_name, execution)
        logger.info(
            "agent_tool_execution",
            extra={
                "tool_name": tool_name,
                "status": execution.status,
                "latency_ms": execution.latency_ms,
                "user_id": user.id,
            },
        )

    def _with_latency(self, tool_name: str, execution: ToolExecution, started_at: float) -> ToolExecution:
        execution.latency_ms = self._elapsed_ms(started_at)
        return execution

    def _elapsed_ms(self, started_at: float) -> int:
        return max(0, int((time.monotonic() - started_at) * 1000))

    async def _calculator(self, params: dict[str, Any], _workspace: Any, _user: UserPublic) -> dict[str, Any]:
        expression = str(params["expression"]).strip()
        result = _safe_eval_arithmetic(expression)
        return {"expression": expression, "result": result}

    async def _course_lookup(self, params: dict[str, Any], _workspace: Any, _user: UserPublic) -> dict[str, Any]:
        query = str(params["query"]).strip().lower()
        catalog = _load_course_catalog()
        courses = [
            course for course in catalog
            if query in str(course["name"]).lower() or query in str(course["code"]).lower()
        ]
        return {"courses": courses, "source": str(_COURSE_CATALOG_PATH)}

    async def _file_content_search(self, params: dict[str, Any], workspace: Any, user: UserPublic) -> dict[str, Any]:
        query = str(params["query"]).strip()
        file_ids = [str(file_id) for file_id in params.get("file_ids", [])]
        visible_files = await workspace.list_files(user)
        if file_ids:
            visible_files = [file for file in visible_files if file.id in file_ids]
        matches = []
        for file_item in visible_files:
            file = await workspace._files.get_by_id(file_item.id) if hasattr(workspace, "_files") else file_item
            if file is None:
                continue
            content_bytes = workspace.read_file_content_for_tool(file)
            if content_bytes is None:
                continue
            content = content_bytes.decode("utf-8", errors="replace")
            index = content.lower().find(query.lower())
            if index < 0 and query.lower() not in file_item.name.lower():
                continue
            start = max(index, 0)
            snippet = content[start:start + 160] if index >= 0 else content[:160]
            matches.append({"file_id": file_item.id, "file_name": file_item.name, "snippet": snippet})
        return {"matches": matches}

    async def _python_data(self, params: dict[str, Any], workspace: Any, user: UserPublic) -> dict[str, Any]:
        file_id = str(params["file_id"])
        file = await workspace._files.get_by_id(file_id)
        if not file:
            raise ValueError("文件不存在或无权访问")
        content_bytes = workspace.read_file_content_for_tool(file)
        if content_bytes is None:
            raise ValueError("无法读取文件内容")
        rows = list(csv.DictReader(io.StringIO(content_bytes.decode("utf-8", errors="replace"))))
        columns = list(rows[0].keys()) if rows else []
        numeric_summary: dict[str, dict[str, float]] = {}
        for column in columns:
            values = []
            for row in rows:
                try:
                    values.append(float(row[column]))
                except (TypeError, ValueError):
                    pass
            if values:
                numeric_summary[column] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                }
        return {"row_count": len(rows), "columns": columns, "numeric_summary": numeric_summary}

    async def _file_compare(self, params: dict[str, Any], workspace: Any, user: UserPublic) -> dict[str, Any]:
        del user
        file_a_id = str(params["file_a"])
        file_b_id = str(params["file_b"])
        if file_a_id == file_b_id:
            raise ValueError("请选择两个不同的文件进行比对")
        file_a = await workspace._files.get_by_id(file_a_id)
        file_b = await workspace._files.get_by_id(file_b_id)
        if not file_a or not file_b:
            raise ValueError("文件不存在或无权访问")
        content_a = workspace.read_file_content_for_tool(file_a)
        content_b = workspace.read_file_content_for_tool(file_b)
        if content_a is None or content_b is None:
            raise ValueError("无法读取待比对文件内容")

        text_a = content_a.decode("utf-8", errors="replace")
        text_b = content_b.decode("utf-8", errors="replace")
        lines_a = text_a.splitlines()
        lines_b = text_b.splitlines()
        matcher = difflib.SequenceMatcher(a=lines_a, b=lines_b, autojunk=False)
        added_lines = 0
        removed_lines = 0
        unchanged_lines = 0
        for tag, a_start, a_end, b_start, b_end in matcher.get_opcodes():
            if tag == "equal":
                unchanged_lines += a_end - a_start
            elif tag == "insert":
                added_lines += b_end - b_start
            elif tag == "delete":
                removed_lines += a_end - a_start
            elif tag == "replace":
                removed_lines += a_end - a_start
                added_lines += b_end - b_start

        context_lines = _bounded_int(params.get("context_lines"), default=3, minimum=0, maximum=10)
        diff = "\n".join(difflib.unified_diff(
            lines_a,
            lines_b,
            fromfile=str(file_a.name),
            tofile=str(file_b.name),
            lineterm="",
            n=context_lines,
        ))
        similarity = round(matcher.ratio(), 4)
        summary = {
            "unchanged_lines": unchanged_lines,
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "similarity": similarity,
            "identical": text_a == text_b,
        }
        report = (
            "# 文件比对报告\n\n"
            f"- 基准文件：{file_a.name}（{len(lines_a)} 行）\n"
            f"- 对比文件：{file_b.name}（{len(lines_b)} 行）\n"
            f"- 相似度：{similarity * 100:.2f}%\n"
            f"- 未变化：{unchanged_lines} 行\n"
            f"- 新增：{added_lines} 行\n"
            f"- 删除：{removed_lines} 行\n\n"
            "## 统一差异\n\n"
            f"```diff\n{diff or '两个文件内容一致'}\n```"
        )
        return {
            "file_a": {"id": file_a_id, "name": file_a.name, "line_count": len(lines_a)},
            "file_b": {"id": file_b_id, "name": file_b.name, "line_count": len(lines_b)},
            "summary": summary,
            "diff": diff,
            "report": report,
        }

    async def _rag_query(self, params: dict[str, Any], workspace: Any, user: UserPublic) -> dict[str, Any]:
        response = await workspace.answer_question(
            QARequest(
                kb_id=str(params["kb_id"]),
                question=str(params["question"]).strip(),
                top_k=int(params.get("top_k") or 8),
            ),
            user,
        )
        return {
            "answer": response.answer,
            "citations": [citation.model_dump() for citation in response.citations],
            "conversation_id": response.conversation_id,
            "message_id": response.message_id,
            "error_code": response.error_code,
        }

    async def _file_metadata_query(self, params: dict[str, Any], workspace: Any, user: UserPublic) -> dict[str, Any]:
        files = await workspace.list_files(user)
        filtered = _filter_file_items(files, params)
        limit = _safe_limit(params.get("limit"), default=20)
        return {
            "total": len(filtered),
            "files": [_file_item_row(file) for file in filtered[:limit]],
        }

    async def _database_query(self, params: dict[str, Any], workspace: Any, user: UserPublic) -> dict[str, Any]:
        table = str(params["table"]).strip()
        limit = _safe_limit(params.get("limit"), default=20)
        query = str(params.get("query") or "").strip().lower()
        if table == "files":
            rows = [_file_item_row(file) for file in _filter_file_items(await workspace.list_files(user), {"query": query})]
            columns = ["id", "name", "type", "size", "parse_status", "tags", "updated_at"]
        elif table == "knowledge_bases":
            rows = [_knowledge_base_row(kb) for kb in await workspace.list_knowledge_bases(user)]
            if query:
                rows = [
                    row for row in rows
                    if query in str(row["name"]).lower()
                    or query in str(row.get("description", "")).lower()
                    or query in " ".join(row.get("tags", [])).lower()
                ]
            columns = ["id", "name", "scope_type", "status", "document_count", "chunk_count", "updated_at"]
        else:
            raise ValueError(f"不允许查询的数据表：{table}")
        return {"table": table, "columns": columns, "rows": rows[:limit], "total": len(rows)}

    async def _weather_lookup(self, params: dict[str, Any], _workspace: Any, _user: UserPublic) -> dict[str, Any]:
        host = os.environ.get("QWEATHER_HOST", "").strip()
        api_key = os.environ.get("QWEATHER_KEY", "").strip()
        if not host:
            raise ValueError("天气工具未配置 QWEATHER_HOST，无法查询天气。")
        if not api_key:
            raise ValueError("天气工具未配置 QWEATHER_KEY，无法查询天气。")

        location = str(params["location"]).strip()
        scheme = "http" if "re.qweatherapi.com" in host else "https"

        # Step 1: City lookup → get location ID
        geo_url = f"{scheme}://{host}/v2/city/lookup?{urllib.parse.urlencode({'location': location, 'key': api_key})}"
        geo_req = urllib.request.Request(geo_url, headers={"Accept": "application/json"})
        geo_body = await asyncio.to_thread(_read_url_text, geo_req, 8)
        try:
            geo_data = json.loads(geo_body)
        except json.JSONDecodeError:
            raise ValueError(f"城市查询返回无效响应: {geo_body[:200]}")

        city_list = geo_data.get("location") if isinstance(geo_data, dict) else None
        if not city_list or not isinstance(city_list, list) or len(city_list) == 0:
            raise ValueError(f"未找到城市「{location}」，请尝试更具体的名称。")

        city_id = city_list[0].get("id")
        city_name = city_list[0].get("name", location)
        if not city_id:
            raise ValueError(f"城市「{location}」缺少 ID，无法查询天气。")

        # Step 2: Weather query → get current weather
        weather_url = f"{scheme}://{host}/v7/weather/now?{urllib.parse.urlencode({'location': city_id, 'key': api_key})}"
        weather_req = urllib.request.Request(weather_url, headers={"Accept": "application/json"})
        weather_body = await asyncio.to_thread(_read_url_text, weather_req, 8)
        try:
            weather_data = json.loads(weather_body)
        except json.JSONDecodeError:
            weather_data = {"raw": weather_body}

        return {
            "location": city_name,
            "city_id": city_id,
            "provider_response": weather_data,
        }

    async def _kb_interest_extract(self, params: dict[str, Any], workspace: Any, user: UserPublic) -> dict[str, Any]:
        kb_id = str(params["kb_id"]).strip()
        max_terms = _bounded_int(params.get("max_terms"), default=8, minimum=1, maximum=20)
        if hasattr(workspace, "list_knowledge_document_profiles"):
            documents = await workspace.list_knowledge_document_profiles(kb_id, user)
        else:
            documents = await workspace.list_knowledge_documents(kb_id, user)
        interests = _extract_interests_from_documents(documents, str(params.get("query") or ""), max_terms=max_terms)
        document_rows = [
            {
                "id": _doc_value(doc, "id"),
                "file_id": _doc_value(doc, "file_id"),
                "file_name": _doc_value(doc, "file_name"),
                "summary": _doc_value(doc, "summary"),
            }
            for doc in documents
        ]
        return {
            "kb_id": kb_id,
            "interests": interests,
            "documents": document_rows,
        }

    async def _arxiv_search(self, params: dict[str, Any], _workspace: Any, _user: UserPublic) -> dict[str, Any]:
        interests = _coerce_string_list(params.get("interests"))
        days = _bounded_int(params.get("days"), default=7, minimum=1, maximum=30)
        max_results = _bounded_int(params.get("max_results"), default=8, minimum=1, maximum=20)
        papers = await asyncio.to_thread(
            _fetch_arxiv_papers,
            interests,
            days=days,
            max_results=max_results,
        )
        return {
            "interests": interests,
            "papers": papers,
            "days": days,
            "max_results": max_results,
        }

    async def _arxiv_markdown_render(self, params: dict[str, Any], _workspace: Any, _user: UserPublic) -> dict[str, Any]:
        interests = _coerce_string_list(params.get("interests"))
        papers = [paper for paper in params.get("papers", []) if isinstance(paper, dict)]
        days = _bounded_int(params.get("days"), default=7, minimum=1, maximum=30)
        markdown = _build_arxiv_markdown_report(interests, papers, days)
        return {
            "markdown": markdown,
            "paper_count": len(papers),
            "interests": interests,
        }

    async def _knowledge_markdown_write(self, params: dict[str, Any], workspace: Any, user: UserPublic) -> dict[str, Any]:
        kb_id = str(params["kb_id"]).strip()
        markdown = str(params["markdown"])
        filename = f"arxiv-interest-report-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.md"
        if str(params.get("filename") or "").strip():
            filename = str(params["filename"]).strip()
        tags = _coerce_string_list(params.get("tags"))
        if not tags:
            tags = ["arxiv", "research-interest", "auto-report"]
        document = await workspace.create_markdown_knowledge_document(
            kb_id,
            filename,
            markdown,
            tags,
            user,
        )
        return {
            "kb_id": kb_id,
            "document_id": document.id,
            "file_id": document.file_id,
            "file_name": document.file_name,
            "markdown": markdown,
        }


_OPERATORS: dict[type[ast.AST], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPERATORS: dict[type[ast.AST], Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _safe_eval_arithmetic(expression: str) -> int | float:
    if not re.fullmatch(r"[\d\s+\-*/().%]+", expression):
        raise ValueError("表达式只能包含数字和算术运算符")
    node = ast.parse(expression, mode="eval")
    result = _eval_node(node.body)
    return int(result) if isinstance(result, float) and result.is_integer() else result


def _read_url_text(request: urllib.request.Request, timeout_seconds: float) -> str:
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - allowlisted tool URL.
        return response.read().decode("utf-8", errors="replace")


def _eval_node(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        op = _OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError("不支持的运算符")
        return op(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op = _UNARY_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError("不支持的一元运算符")
        return op(_eval_node(node.operand))
    raise ValueError("不支持的表达式")


def _load_course_catalog() -> list[dict[str, Any]]:
    try:
        data = json.loads(_COURSE_CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"课程目录读取失败：{exc}") from exc
    if not isinstance(data, list):
        raise ValueError("课程目录格式错误")
    return [item for item in data if isinstance(item, dict)]


def _filter_file_items(files: list[Any], params: dict[str, Any]) -> list[Any]:
    query = str(params.get("query") or "").strip().lower()
    tag = str(params.get("tag") or "").strip().lower()
    file_type = str(params.get("type") or "").strip().lower()
    parse_status = str(params.get("parse_status") or "").strip().lower()
    result = []
    for file in files:
        tags = [str(item).lower() for item in getattr(file, "tags", [])]
        name = str(getattr(file, "name", "")).lower()
        if query and query not in name and query not in " ".join(tags):
            continue
        if tag and tag not in tags:
            continue
        if file_type and str(getattr(file, "type", "")).lower() != file_type:
            continue
        if parse_status and str(getattr(file, "parse_status", "")).lower() != parse_status:
            continue
        result.append(file)
    return result


def _file_item_row(file: Any) -> dict[str, Any]:
    return {
        "id": getattr(file, "id", ""),
        "name": getattr(file, "name", ""),
        "folder_id": getattr(file, "folder_id", ""),
        "type": getattr(file, "type", ""),
        "size": getattr(file, "size", 0),
        "parse_status": getattr(file, "parse_status", ""),
        "tags": list(getattr(file, "tags", []) or []),
        "updated_at": str(getattr(file, "updated_at", "")),
        "permission_scope": getattr(file, "permission_scope", ""),
        "knowledge_base_ids": list(getattr(file, "knowledge_base_ids", []) or []),
    }


def _knowledge_base_row(kb: Any) -> dict[str, Any]:
    return {
        "id": getattr(kb, "id", ""),
        "name": getattr(kb, "name", ""),
        "description": getattr(kb, "description", ""),
        "scope_type": getattr(kb, "scope_type", ""),
        "scope_id": getattr(kb, "scope_id", None),
        "tags": list(getattr(kb, "tags", []) or []),
        "status": getattr(kb, "status", ""),
        "document_count": getattr(kb, "document_count", 0),
        "chunk_count": getattr(kb, "chunk_count", 0),
        "updated_at": str(getattr(kb, "updated_at", "")),
    }


def _safe_limit(value: Any, default: int) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(limit, 100))


def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(number, maximum))


def _coerce_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        raw_items = re.split(r"[,，;；\n]+", value)
    elif isinstance(value, list):
        raw_items = value
    else:
        raw_items = []
    return [str(item).strip() for item in raw_items if str(item).strip()]


def _extract_interests_from_documents(documents: list[Any], explicit_query: str = "", *, max_terms: int = 8) -> list[str]:
    candidates: list[str] = []
    if explicit_query.strip():
        candidates.extend(_split_interest_terms(explicit_query))
    for doc in documents:
        if isinstance(doc, dict):
            values = [
                str(doc.get("summary") or ""),
                str(doc.get("file_name") or ""),
                str(doc.get("content_preview") or ""),
                " ".join(str(item) for item in doc.get("keywords", []) if item),
                " ".join(str(item) for item in doc.get("outline", []) if item),
            ]
        else:
            values = [
                getattr(doc, "summary", "") or "",
                getattr(doc, "file_name", "") or "",
            ]
        for value in values:
            candidates.extend(_split_interest_terms(value))
    scored: dict[str, int] = {}
    for term in candidates:
        normalized = _normalize_interest(term)
        if not normalized or normalized in _INTEREST_STOPWORDS:
            continue
        if len(normalized) < 2:
            continue
        scored[normalized] = scored.get(normalized, 0) + 1
    ranked = sorted(scored.items(), key=lambda item: (-item[1], item[0]))
    return [term for term, _ in ranked[:max_terms]] or ["machine learning"]


def _doc_value(doc: Any, key: str) -> Any:
    if isinstance(doc, dict):
        return doc.get(key, "")
    return getattr(doc, key, "")


def _split_interest_terms(text: str) -> list[str]:
    text = re.sub(r"[_/\\|]+", " ", text)
    phrases = re.findall(r"[A-Za-z][A-Za-z0-9\- ]{2,48}|[\u4e00-\u9fff]{2,12}", text)
    terms: list[str] = []
    for phrase in phrases:
        cleaned = phrase.strip(" -:：，。,.()[]{}")
        if not cleaned:
            continue
        if re.search(r"[\u4e00-\u9fff]", cleaned):
            terms.append(cleaned)
        else:
            words = [word for word in re.split(r"\s+", cleaned.lower()) if word]
            if 1 <= len(words) <= 4:
                terms.append(" ".join(words))
            for word in words:
                if len(word) >= 4:
                    terms.append(word)
    return terms


def _normalize_interest(term: str) -> str:
    term = re.sub(r"\s+", " ", term.strip().lower())
    return term.strip(" -:：，。,.()[]{}")


def _fetch_arxiv_papers(interests: list[str], *, days: int, max_results: int) -> list[dict[str, Any]]:
    query_terms = [term for term in interests[:5] if term]
    query = " OR ".join(f'all:"{term}"' for term in query_terms) or 'all:"machine learning"'
    params = urllib.parse.urlencode({
        "search_query": query,
        "start": 0,
        "max_results": max_results * 3,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    url = f"https://export.arxiv.org/api/query?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "whucs-training-project/1.0"})
    with urllib.request.urlopen(request, timeout=12) as response:  # noqa: S310 - arXiv public API endpoint.
        body = response.read()
    papers = _parse_arxiv_feed(body)
    cutoff = datetime.now(UTC) - timedelta(days=days)
    recent = [
        paper for paper in papers
        if paper.get("published_at") is None or paper["published_at"] >= cutoff
    ]
    return [_paper_public_payload(paper) for paper in recent[:max_results]]


def _parse_arxiv_feed(body: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(body)
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    papers: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns):
        published_raw = _xml_text(entry, "atom:published", ns)
        published_at = _parse_arxiv_datetime(published_raw)
        link = ""
        pdf_url = ""
        for node in entry.findall("atom:link", ns):
            href = node.attrib.get("href", "")
            if node.attrib.get("title") == "pdf":
                pdf_url = href
            elif node.attrib.get("rel") == "alternate":
                link = href
        papers.append({
            "id": _xml_text(entry, "atom:id", ns),
            "title": _clean_space(_xml_text(entry, "atom:title", ns)),
            "summary": _clean_space(_xml_text(entry, "atom:summary", ns)),
            "authors": [
                _xml_text(author, "atom:name", ns)
                for author in entry.findall("atom:author", ns)
                if _xml_text(author, "atom:name", ns)
            ],
            "published": published_raw,
            "published_at": published_at,
            "updated": _xml_text(entry, "atom:updated", ns),
            "link": link,
            "pdf_url": pdf_url,
            "categories": [node.attrib.get("term", "") for node in entry.findall("atom:category", ns)],
        })
    return papers


def _paper_public_payload(paper: dict[str, Any]) -> dict[str, Any]:
    payload = dict(paper)
    payload.pop("published_at", None)
    payload["abstract"] = payload.pop("summary", "")
    return payload


def _build_arxiv_markdown_report(interests: list[str], papers: list[dict[str, Any]], days: int) -> str:
    lines = [
        "# arXiv 近期论文推荐",
        "",
        f"- 生成时间：{datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        f"- 时间范围：最近 {days} 天",
        f"- 兴趣关键词：{', '.join(interests)}",
        "",
    ]
    if not papers:
        lines.extend([
            "## 未找到匹配论文",
            "",
            "本次查询没有返回近几天内匹配兴趣关键词的 arXiv 论文。可以扩大时间范围或补充更具体的研究方向。",
            "",
        ])
        return "\n".join(lines)
    lines.append("## 论文列表")
    lines.append("")
    for index, paper in enumerate(papers, 1):
        authors = ", ".join(paper.get("authors", [])[:5]) or "Unknown authors"
        abstract = str(paper.get("abstract", "")).strip()
        if len(abstract) > 700:
            abstract = f"{abstract[:700].rstrip()}..."
        lines.extend([
            f"### {index}. {paper.get('title', 'Untitled')}",
            "",
            f"- 作者：{authors}",
            f"- 发布时间：{paper.get('published', '')}",
            f"- 分类：{', '.join(paper.get('categories', []))}",
            f"- 链接：{paper.get('link') or paper.get('id')}",
            f"- PDF：{paper.get('pdf_url', '')}",
            "",
            abstract,
            "",
        ])
    return "\n".join(lines)


def _xml_text(node: ET.Element, path: str, ns: dict[str, str]) -> str:
    child = node.find(path, ns)
    return child.text.strip() if child is not None and child.text else ""


def _parse_arxiv_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _clean_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


_INTEREST_STOPWORDS = {
    "and",
    "are",
    "arxiv",
    "for",
    "from",
    "markdown",
    "paper",
    "report",
    "the",
    "with",
    "文档",
    "报告",
    "论文",
    "知识库",
}
