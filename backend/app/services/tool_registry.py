from __future__ import annotations

import ast
import csv
import io
import operator
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from app.domain.schemas import ToolDefinition, UserPublic


ToolHandler = Callable[[dict[str, Any], Any, UserPublic], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ToolSpec:
    definition: ToolDefinition
    handler: ToolHandler
    clarification: str


@dataclass
class ToolExecution:
    status: str
    output: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    clarification: str | None = None


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
        }

    def definitions(self) -> list[ToolDefinition]:
        return [spec.definition for spec in self._tools.values()]

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    async def execute(self, name: str, params: dict[str, Any], workspace: Any, user: UserPublic) -> ToolExecution:
        spec = self.get(name)
        if spec is None:
            return ToolExecution(status="failed", error_message=f"未知工具：{name}")
        missing = self._missing_required(spec.definition, params)
        if missing:
            return ToolExecution(status="needs_clarification", clarification=spec.clarification)
        try:
            output = await spec.handler(params, workspace, user)
        except Exception as exc:
            return ToolExecution(status="failed", error_message=str(exc))
        return ToolExecution(status="success", output=output)

    def _missing_required(self, definition: ToolDefinition, params: dict[str, Any]) -> list[str]:
        missing: list[str] = []
        for key in definition.input_schema.get("required", []):
            value = params.get(key)
            if value is None or value == "" or value == []:
                missing.append(str(key))
        return missing

    async def _calculator(self, params: dict[str, Any], _workspace: Any, _user: UserPublic) -> dict[str, Any]:
        expression = str(params["expression"]).strip()
        result = _safe_eval_arithmetic(expression)
        return {"expression": expression, "result": result}

    async def _course_lookup(self, params: dict[str, Any], _workspace: Any, _user: UserPublic) -> dict[str, Any]:
        query = str(params["query"]).strip().lower()
        catalog = [
            {"code": "CS101", "name": "算法设计", "teacher": "王老师", "credits": 3},
            {"code": "CS204", "name": "数据库系统", "teacher": "李老师", "credits": 3},
            {"code": "AI301", "name": "机器学习", "teacher": "陈老师", "credits": 2},
        ]
        courses = [
            course for course in catalog
            if query in course["name"].lower() or query in course["code"].lower()
        ]
        return {"courses": courses}

    async def _file_content_search(self, params: dict[str, Any], workspace: Any, user: UserPublic) -> dict[str, Any]:
        query = str(params["query"]).strip()
        file_ids = [str(file_id) for file_id in params.get("file_ids", [])]
        files = await workspace._files.list_all()
        if file_ids:
            files = [file for file in files if file.id in file_ids]
        matches = []
        for file in files:
            if file.created_by != user.username:
                continue
            content_bytes = workspace.read_file_content_for_tool(file)
            if content_bytes is None:
                continue
            content = content_bytes.decode("utf-8", errors="replace")
            index = content.lower().find(query.lower())
            if index < 0 and query.lower() not in file.name.lower():
                continue
            start = max(index, 0)
            snippet = content[start:start + 160] if index >= 0 else content[:160]
            matches.append({"file_id": file.id, "file_name": file.name, "snippet": snippet})
        return {"matches": matches}

    async def _python_data(self, params: dict[str, Any], workspace: Any, user: UserPublic) -> dict[str, Any]:
        file_id = str(params["file_id"])
        file = await workspace._files.get_by_id(file_id)
        if not file or file.created_by != user.username:
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
