from __future__ import annotations

import json
import logging
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.services.llm import _get_llm
from app.services.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class PlannedToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""


class AgentPlan(BaseModel):
    intent: str = ""
    missing_fields: list[str] = Field(default_factory=list)
    plan_steps: list[PlannedToolCall] = Field(default_factory=list)
    answer_strategy: str = "direct"


class ToolCallingLLM:
    def __init__(self, llm: Any | None = None) -> None:
        self._llm = llm

    def _client(self) -> Any | None:
        return self._llm if self._llm is not None else _get_llm()

    def available(self) -> bool:
        return self._client() is not None

    async def complete(self, prompt: str) -> str | None:
        llm = self._client()
        if llm is None:
            return None
        response = llm.invoke(prompt)
        return response.content.strip() if hasattr(response, "content") else str(response).strip()


class AgentPlanner:
    def __init__(self, registry: ToolRegistry | None = None, tool_llm: ToolCallingLLM | None = None) -> None:
        self._registry = registry or ToolRegistry()
        self._tool_llm = tool_llm or ToolCallingLLM()

    async def plan(
        self,
        task: str,
        context_file_ids: list[str],
        kb_id: str | None,
        inputs: dict[str, Any],
    ) -> AgentPlan:
        fallback = self.fallback_plan(task, context_file_ids, kb_id, inputs)
        if inputs.get("_history") and not fallback.plan_steps and not _explicit_tool_request(task):
            return fallback
        if not self._tool_llm.available():
            return fallback

        prompt = self._build_prompt(task, context_file_ids, kb_id, inputs)
        try:
            raw_plan = await self._tool_llm.complete(prompt)
        except Exception:
            logger.warning("Agent planner LLM call failed, using fallback", exc_info=True)
            return fallback
        parsed = self._parse_plan(raw_plan or "")
        if parsed is None:
            return fallback
        normalized = self._normalize_plan(parsed, task, context_file_ids, kb_id, inputs)
        if not normalized.plan_steps and not normalized.missing_fields and fallback.plan_steps:
            return fallback
        return normalized

    async def revise(
        self,
        task: str,
        context_file_ids: list[str],
        kb_id: str | None,
        inputs: dict[str, Any],
        *,
        previous_plan: AgentPlan,
        observations: list[dict[str, Any]],
        reason: str,
    ) -> AgentPlan:
        if not self._tool_llm.available():
            return AgentPlan(intent="无需修正规划", answer_strategy="answer_from_observations")

        prompt = self._build_revision_prompt(
            task,
            context_file_ids,
            kb_id,
            inputs,
            previous_plan,
            observations,
            reason,
        )
        try:
            raw_plan = await self._tool_llm.complete(prompt)
        except Exception:
            logger.warning("Agent planner revision LLM call failed, using current observations", exc_info=True)
            return AgentPlan(intent="修正规划失败", answer_strategy="answer_from_observations")
        parsed = self._parse_plan(raw_plan or "")
        if parsed is None:
            return AgentPlan(intent="修正规划失败", answer_strategy="answer_from_observations")
        return self._normalize_plan(parsed, task, context_file_ids, kb_id, inputs)

    def fallback_plan(
        self,
        task: str,
        context_file_ids: list[str],
        kb_id: str | None,
        inputs: dict[str, Any],
    ) -> AgentPlan:
        planned: list[PlannedToolCall] = []
        if _is_arxiv_interest_task(task):
            planned.extend([
                PlannedToolCall(
                    tool_name="kb_interest_extract",
                    arguments={
                        "kb_id": inputs.get("kb_id") or kb_id or "",
                        "query": inputs.get("query") or "",
                        "max_terms": inputs.get("max_terms") or 8,
                    },
                    rationale="读取知识库文档并提取兴趣关键词",
                ),
                PlannedToolCall(
                    tool_name="arxiv_search",
                    arguments={
                        "interests": "$kb_interest_extract.interests",
                        "days": inputs.get("days") or _extract_days(task),
                        "max_results": inputs.get("max_results") or _extract_max_results(task),
                    },
                    rationale="根据兴趣关键词查询 arXiv 近期论文",
                ),
                PlannedToolCall(
                    tool_name="arxiv_markdown_render",
                    arguments={
                        "interests": "$kb_interest_extract.interests",
                        "papers": "$arxiv_search.papers",
                        "days": inputs.get("days") or _extract_days(task),
                    },
                    rationale="把论文列表整理成 Markdown 报告",
                ),
                PlannedToolCall(
                    tool_name="knowledge_markdown_write",
                    arguments={
                        "kb_id": inputs.get("kb_id") or kb_id or "",
                        "markdown": "$arxiv_markdown_render.markdown",
                        "tags": ["arxiv", "research-interest", "auto-report"],
                    },
                    rationale="把 Markdown 报告写回知识库",
                ),
            ])
        if "计算" in task or re.search(r"\d+\s*[-+*/]", task):
            planned.append(PlannedToolCall(
                tool_name="calculator",
                arguments={"expression": inputs.get("expression") or _extract_expression(task)},
                rationale="执行算术计算",
            ))
        if "课程" in task and "知识库" not in task and "rag" not in task.lower():
            query = inputs.get("query") or _extract_course_query(task)
            planned.append(PlannedToolCall(
                tool_name="course_lookup",
                arguments={"query": query},
                rationale="查询课程目录",
            ))
        if _is_file_metadata_task(task):
            planned.append(PlannedToolCall(
                tool_name="file_metadata_query",
                arguments={
                    "query": inputs.get("query") or _extract_file_metadata_query(task),
                    "tag": inputs.get("tag") or "",
                    "type": inputs.get("type") or "",
                    "parse_status": inputs.get("parse_status") or _extract_parse_status(task),
                },
                rationale="查询文件元数据",
            ))
        elif "文件" in task or context_file_ids:
            planned.append(PlannedToolCall(
                tool_name="file_content_search",
                arguments={
                    "query": inputs.get("query") or _extract_search_query(task),
                    "file_ids": inputs.get("file_ids") or context_file_ids,
                    "kb_id": kb_id,
                },
                rationale="搜索可访问文件内容",
            ))
        if "csv" in task.lower() or ("数据" in task and context_file_ids):
            planned.append(PlannedToolCall(
                tool_name="python_data",
                arguments={"file_id": inputs.get("file_id") or (context_file_ids[0] if context_file_ids else "")},
                rationale="分析 CSV 数据文件",
            ))
        if "数据库" in task or "数据表" in task:
            planned.append(PlannedToolCall(
                tool_name="database_query",
                arguments={
                    "table": inputs.get("table") or _extract_database_table(task),
                    "query": inputs.get("query") or _extract_database_query(task),
                },
                rationale="查询受限只读数据表",
            ))
        elif not _is_arxiv_interest_task(task) and ("知识库" in task or "rag" in task.lower() or inputs.get("kb_id") or kb_id):
            if "知识库" in task or "rag" in task.lower() or inputs.get("question"):
                planned.append(PlannedToolCall(
                    tool_name="rag_query",
                    arguments={
                        "kb_id": inputs.get("kb_id") or kb_id or "",
                        "question": inputs.get("question") or _extract_rag_question(task),
                    },
                    rationale="查询知识库生成回答",
                ))
        if "天气" in task:
            planned.append(PlannedToolCall(
                tool_name="weather_lookup",
                arguments={"location": inputs.get("location") or _extract_weather_location(task)},
                rationale="查询真实天气服务",
            ))

        deduped: list[PlannedToolCall] = []
        seen: set[str] = set()
        for step in planned:
            if step.tool_name not in seen:
                deduped.append(step)
                seen.add(step.tool_name)

        missing_fields: list[str] = []
        for step in deduped:
            spec = self._registry.get(step.tool_name)
            if spec is None:
                continue
            for field in spec.definition.input_schema.get("required", []):
                value = step.arguments.get(str(field))
                if value is None or value == "" or value == []:
                    missing_fields.append(str(field))

        return AgentPlan(
            intent=_describe_intent(deduped, task),
            missing_fields=_unique(missing_fields),
            plan_steps=deduped,
            answer_strategy="direct" if not deduped else "use_tools_then_answer",
        )

    def _build_prompt(
        self,
        task: str,
        context_file_ids: list[str],
        kb_id: str | None,
        inputs: dict[str, Any],
    ) -> str:
        tools = [definition.model_dump() for definition in self._registry.definitions()]
        schema = {
            "intent": "string",
            "missing_fields": ["string"],
            "plan_steps": [
                {
                    "tool_name": "one of available tool names",
                    "arguments": {"param": "value"},
                    "rationale": "short user-visible reason, no hidden reasoning",
                }
            ],
            "answer_strategy": "string",
        }
        return (
            "你是工具调用规划器。根据用户任务选择必要工具，并只输出一个 JSON 对象。\n"
            "禁止输出 Markdown、解释文字或隐藏推理。rationale 只能是一句面向用户的简短理由。\n"
            "如果用户信息不足，把缺失字段写入 missing_fields，并保留相应工具步骤的空参数。\n\n"
            f"【输出结构】\n{json.dumps(schema, ensure_ascii=False)}\n\n"
            f"【可用工具】\n{json.dumps(tools, ensure_ascii=False)}\n\n"
            f"【用户任务】{task}\n"
            f"【上下文文件】{json.dumps(context_file_ids, ensure_ascii=False)}\n"
            f"【知识库】{kb_id or ''}\n"
            f"【补充输入】{json.dumps(inputs, ensure_ascii=False)}"
        )

    def _build_revision_prompt(
        self,
        task: str,
        context_file_ids: list[str],
        kb_id: str | None,
        inputs: dict[str, Any],
        previous_plan: AgentPlan,
        observations: list[dict[str, Any]],
        reason: str,
    ) -> str:
        return (
            f"{self._build_prompt(task, context_file_ids, kb_id, inputs)}\n\n"
            "【上一版计划】\n"
            f"{previous_plan.model_dump_json()}\n\n"
            "【已有观察】\n"
            f"{json.dumps(observations, ensure_ascii=False)}\n\n"
            f"【需要修正的原因】{reason}\n"
            "请只输出下一步需要追加执行的 JSON 计划；如果不需要新工具，plan_steps 返回空数组。"
        )

    def _parse_plan(self, raw_plan: str) -> AgentPlan | None:
        candidate = _extract_json_object(raw_plan)
        if not candidate:
            return None
        try:
            return AgentPlan.model_validate(json.loads(candidate))
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError):
            logger.info("Invalid agent planner JSON, using fallback", exc_info=True)
            return None

    def _normalize_plan(
        self,
        plan: AgentPlan,
        task: str,
        context_file_ids: list[str],
        kb_id: str | None,
        inputs: dict[str, Any],
    ) -> AgentPlan:
        valid_tool_names = {definition.name for definition in self._registry.definitions()}
        fallback_steps = self.fallback_plan(task, context_file_ids, kb_id, inputs).plan_steps
        fallback_by_tool = {step.tool_name: step for step in fallback_steps}
        fallback_tool_names = set(fallback_by_tool)
        steps: list[PlannedToolCall] = []
        seen: set[str] = set()
        missing_fields: list[str] = list(plan.missing_fields)
        for step in plan.plan_steps:
            if step.tool_name not in valid_tool_names or step.tool_name in seen:
                continue
            arguments = dict(step.arguments)
            if step.tool_name == "file_content_search":
                arguments.setdefault("file_ids", inputs.get("file_ids") or context_file_ids)
                arguments.setdefault("kb_id", kb_id)
                arguments.setdefault("query", inputs.get("query") or _extract_search_query(task))
            elif step.tool_name == "python_data":
                arguments.setdefault("file_id", inputs.get("file_id") or (context_file_ids[0] if context_file_ids else ""))
            elif step.tool_name == "course_lookup":
                arguments.setdefault("query", inputs.get("query") or _extract_course_query(task))
            elif step.tool_name == "calculator":
                arguments.setdefault("expression", inputs.get("expression") or _extract_expression(task))
                fallback_step = fallback_by_tool.get(step.tool_name)
                fallback_expression = fallback_step.arguments.get("expression") if fallback_step else None
                if fallback_expression:
                    arguments["expression"] = fallback_expression
            elif step.tool_name == "rag_query":
                arguments.setdefault("kb_id", inputs.get("kb_id") or kb_id or "")
                arguments.setdefault("question", inputs.get("question") or _extract_rag_question(task))
            elif step.tool_name == "file_metadata_query":
                arguments.setdefault("query", inputs.get("query") or _extract_file_metadata_query(task))
            elif step.tool_name == "database_query":
                arguments.setdefault("table", inputs.get("table") or _extract_database_table(task))
                arguments.setdefault("query", inputs.get("query") or _extract_database_query(task))
            elif step.tool_name == "weather_lookup":
                arguments.setdefault("location", inputs.get("location") or _extract_weather_location(task))
            elif step.tool_name == "kb_interest_extract":
                arguments.setdefault("kb_id", inputs.get("kb_id") or kb_id or "")
                arguments.setdefault("query", inputs.get("query") or "")
                arguments.setdefault("max_terms", inputs.get("max_terms") or 8)
            elif step.tool_name == "arxiv_search":
                arguments.setdefault("interests", "$kb_interest_extract.interests")
                arguments.setdefault("days", inputs.get("days") or _extract_days(task))
                arguments.setdefault("max_results", inputs.get("max_results") or _extract_max_results(task))
            elif step.tool_name == "arxiv_markdown_render":
                arguments.setdefault("interests", "$kb_interest_extract.interests")
                arguments.setdefault("papers", "$arxiv_search.papers")
                arguments.setdefault("days", inputs.get("days") or _extract_days(task))
            elif step.tool_name == "knowledge_markdown_write":
                arguments.setdefault("kb_id", inputs.get("kb_id") or kb_id or "")
                arguments.setdefault("markdown", "$arxiv_markdown_render.markdown")
                arguments.setdefault("tags", ["arxiv", "research-interest", "auto-report"])

            spec = self._registry.get(step.tool_name)
            step_missing: list[str] = []
            if spec:
                for field in spec.definition.input_schema.get("required", []):
                    value = arguments.get(str(field))
                    if value is None or value == "" or value == []:
                        fallback_step = fallback_by_tool.get(step.tool_name)
                        fallback_value = fallback_step.arguments.get(str(field)) if fallback_step else None
                        if fallback_value is not None and fallback_value != "" and fallback_value != []:
                            arguments[str(field)] = fallback_value
                        else:
                            step_missing.append(str(field))
                if step_missing and step.tool_name not in fallback_tool_names:
                    continue
                missing_fields.extend(step_missing)
            steps.append(PlannedToolCall(
                tool_name=step.tool_name,
                arguments=arguments,
                rationale=_public_rationale(step.rationale),
            ))
            seen.add(step.tool_name)

        # Normalize $stepN.field → $tool_name.field references from LLM output
        step_index_to_name: dict[str, str] = {}
        for i, s in enumerate(steps):
            for prefix in (str(i + 1), str(i)):
                step_index_to_name[f"step{prefix}"] = s.tool_name
        _step_ref = re.compile(r"\$step(\d+)\.(\w+)")
        for s in steps:
            for key, value in list(s.arguments.items()):
                if isinstance(value, str):
                    s.arguments[key] = _step_ref.sub(
                        lambda m: f"${step_index_to_name.get(f'step{m.group(1)}', m.group(0))}.{m.group(2)}",
                        value,
                    )

        return AgentPlan(
            intent=plan.intent or _describe_intent(steps, task),
            missing_fields=_unique(missing_fields),
            plan_steps=steps,
            answer_strategy=plan.answer_strategy or ("direct" if not steps else "use_tools_then_answer"),
        )


def _extract_json_object(raw: str) -> str | None:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        return fence.group(1)
    if text.startswith("{") and text.endswith("}"):
        return text
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start:end + 1]
    return None


def _extract_expression(task: str) -> str:
    match = re.search(r"计算\s*(.+)$", task)
    expression = match.group(1).strip() if match else task.strip()
    expression = re.split(r"\s*(?:并|然后|再|，|,)\s*(?:查询|搜索|分析|在文件|课程)", expression, maxsplit=1)[0]
    return expression.strip()


def _extract_course_query(task: str) -> str:
    match = re.search(r"(?:查询|搜索|了解)\s*([\w\u4e00-\u9fff]*?)课程(?:信息)?", task)
    if match:
        return match.group(1).strip()
    cleaned = task.replace("课程信息", "").replace("课程", "").replace("查询", "").strip()
    cleaned = re.split(r"\s*(?:并|然后|再|，|,)\s*", cleaned)[-1].strip()
    return "" if not cleaned else cleaned


def _extract_search_query(task: str) -> str:
    match = re.search(r"查询\s+(.+)$", task)
    return match.group(1).strip() if match else task.strip()


def _is_file_metadata_task(task: str) -> bool:
    return "文件" in task and any(keyword in task for keyword in ("列表", "元数据", "状态", "有哪些", "大小", "标签"))


def _explicit_tool_request(task: str) -> bool:
    lowered = task.lower()
    return (
        "计算" in task
        or bool(re.search(r"\d+\s*[-+*/]", task))
        or "课程" in task
        or "文件" in task
        or "csv" in lowered
        or "数据" in task
        or "数据库" in task
        or "数据表" in task
        or "知识库" in task
        or "rag" in lowered
        or "天气" in task
    )


def _extract_file_metadata_query(task: str) -> str:
    cleaned = task
    for token in ("查询", "搜索", "文件列表", "文件元数据", "文件状态", "有哪些文件", "文件"):
        cleaned = cleaned.replace(token, " ")
    return " ".join(cleaned.split()).strip()


def _extract_parse_status(task: str) -> str:
    if "失败" in task:
        return "failed"
    if "已解析" in task or "已索引" in task:
        return "indexed"
    if "解析中" in task:
        return "parsing"
    if "排队" in task:
        return "queued"
    return ""


def _extract_rag_question(task: str) -> str:
    cleaned = task.replace("知识库", "").replace("RAG", "").replace("rag", "").replace("查询", "").strip()
    return cleaned or task.strip()


def _extract_database_table(task: str) -> str:
    if "知识库" in task:
        return "knowledge_bases"
    if "文件" in task:
        return "files"
    return ""


def _extract_database_query(task: str) -> str:
    cleaned = task.replace("数据库", "").replace("数据表", "").replace("查询", "").strip()
    return cleaned


def _extract_weather_location(task: str) -> str:
    match = re.search(r"(?:查询|看看|获取)?\s*([\w\u4e00-\u9fff]+?)天气", task)
    if match:
        return match.group(1).strip()
    cleaned = task.replace("天气", "").replace("查询", "").strip()
    return cleaned


def _is_arxiv_interest_task(task: str) -> bool:
    lowered = task.lower()
    return (
        "arxiv" in lowered
        and ("知识库" in task or "文档" in task or "兴趣" in task)
        and ("论文" in task or "paper" in lowered)
    )


def _extract_days(task: str) -> int:
    match = re.search(r"(?:近|最近)\s*(\d+)\s*(?:天|日|days?)", task, flags=re.IGNORECASE)
    if match:
        return max(1, min(int(match.group(1)), 30))
    if "几天" in task or "近期" in task or "最近" in task:
        return 7
    return 7


def _extract_max_results(task: str) -> int:
    match = re.search(r"(\d+)\s*(?:篇|papers?)", task, flags=re.IGNORECASE)
    if match:
        return max(1, min(int(match.group(1)), 20))
    return 8


def _describe_intent(steps: list[PlannedToolCall], task: str) -> str:
    tools = [step.tool_name for step in steps]
    if tools == ["calculator", "course_lookup"]:
        return "计算并查询课程"
    if tools == ["kb_interest_extract", "arxiv_search", "arxiv_markdown_render", "knowledge_markdown_write"]:
        return "生成 arXiv 兴趣论文报告"
    if not tools:
        return "直接回答"
    return "、".join(tools) or task[:40]


def _public_rationale(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or "chain" in cleaned.lower() or "thought" in cleaned.lower():
        return "执行该步骤所需的工具调用"
    return cleaned[:120]


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
