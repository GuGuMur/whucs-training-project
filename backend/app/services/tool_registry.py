from __future__ import annotations

import ast
import csv
import io
import json
import logging
import operator
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
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
        if "weather_lookup" in self._tools and not os.environ.get("WEATHER_API_URL", "").strip():
            issues.append({
                "tool": "weather_lookup",
                "code": "WEATHER_API_URL_MISSING",
                "message": "天气工具未配置 WEATHER_API_URL。",
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
        if name in {"file_content_search", "python_data"}:
            visible_files = await workspace.list_files(user)
            visible_ids = {str(getattr(file, "id", "")) for file in visible_files}
            requested_ids = [str(item) for item in params.get("file_ids", [])] if name == "file_content_search" else [str(params.get("file_id", ""))]
            requested_ids = [item for item in requested_ids if item]
            denied = [file_id for file_id in requested_ids if file_id not in visible_ids]
            if denied:
                raise PermissionError(f"文件不存在或无权访问：{', '.join(denied)}")
        elif name == "rag_query" and hasattr(workspace, "_ensure_kb_access"):
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
        base_url = os.environ.get("WEATHER_API_URL", "").strip()
        api_key = os.environ.get("WEATHER_API_KEY", "").strip()
        if not base_url:
            raise ValueError("天气工具未配置真实 WEATHER_API_URL，无法查询天气。")

        location = str(params["location"]).strip()
        query_params = {"location": location}
        if api_key:
            query_params["key"] = api_key
        separator = "&" if "?" in base_url else "?"
        url = f"{base_url}{separator}{urllib.parse.urlencode(query_params)}"
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=8) as response:  # noqa: S310 - URL is operator-configured.
            body = response.read().decode("utf-8", errors="replace")
        try:
            provider_response = json.loads(body)
        except json.JSONDecodeError:
            provider_response = {"raw": body}
        return {"location": location, "provider_response": provider_response}


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
