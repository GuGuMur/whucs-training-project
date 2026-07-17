from __future__ import annotations

import asyncio
import re
import secrets
import time
from typing import Any

from app.domain.schemas import AgentPlanPreviewResponse, AgentPlanPreviewStep, AgentStep, AgentTaskResponse, UserPublic
from app.services.agent_planner import AgentPlan, AgentPlanner, PlannedToolCall
from app.services.tool_registry import ToolRegistry


_AGENT_TASKS: dict[str, AgentTaskResponse] = {}
_AGENT_OWNERS: dict[str, int] = {}
_AGENT_REQUESTS: dict[str, dict[str, Any]] = {}


class AgentExecutor:
    def __init__(
        self,
        registry: ToolRegistry | None = None,
        planner: AgentPlanner | None = None,
        *,
        max_tool_calls: int = 6,
        max_retries_per_tool: int = 2,
        max_runtime_seconds: float = 120.0,
    ) -> None:
        self._registry = registry or ToolRegistry()
        self._planner = planner or AgentPlanner(self._registry)
        self._max_tool_calls = max_tool_calls
        self._max_retries_per_tool = max_retries_per_tool
        if max_runtime_seconds <= 0:
            raise ValueError("max_runtime_seconds must be greater than zero")
        self._max_runtime_seconds = max_runtime_seconds

    async def run(
        self,
        payload: Any,
        workspace: Any,
        user: UserPublic,
        *,
        task_id: str | None = None,
        continuation_inputs: dict[str, Any] | None = None,
    ) -> AgentTaskResponse:
        task = getattr(payload, "task", "")
        context_file_ids = list(getattr(payload, "context_file_ids", []) or [])
        kb_id = getattr(payload, "kb_id", None)
        request = {
            "task": task,
            "context_file_ids": context_file_ids,
            "kb_id": kb_id,
            "inputs": continuation_inputs or {},
        }
        task_id = task_id or f"agent-{secrets.token_hex(4)}"
        started_at = time.monotonic()
        steps: list[AgentStep] = [
            AgentStep(
                type="thought",
                phase="understand",
                title="理解任务",
                content=f"识别用户任务：{task}",
            ),
        ]
        try:
            plan = await asyncio.wait_for(
                self._planner.plan(task, context_file_ids, kb_id, request["inputs"]),
                timeout=self._remaining_seconds(started_at),
            )
        except TimeoutError:
            return self._runtime_timeout_response(
                task_id, task, steps, user, request, phase="plan",
            )
        pending_steps = list(plan.plan_steps)
        plan_label = self._plan_label(pending_steps)
        steps.append(
            AgentStep(
                type="thought",
                phase="plan",
                title="规划步骤",
                content=f"选择工具：{plan_label}",
                tool_name=pending_steps[0].tool_name if len(pending_steps) == 1 else None,
                input_json=self._plan_input_json(plan),
            ),
        )

        if not pending_steps:
            final_answer = self._direct_answer(task, request["inputs"])
            response = AgentTaskResponse(
                id=task_id,
                task=task,
                status="completed",
                steps=[
                    *steps,
                    AgentStep(
                        type="answer",
                        phase="answer",
                        title="最终回答",
                        content=final_answer,
                        output_json={"answer": final_answer},
                    ),
                ],
                final_answer=final_answer,
                result_view={"type": "text", "content": final_answer},
            )
            self._save(response, user, request)
            return response

        observations: list[tuple[str, dict[str, Any], str, str]] = []
        raw_observations: list[dict[str, Any]] = []
        retry_counts: dict[str, int] = {}
        tool_call_count = 0
        while pending_steps:
            if tool_call_count >= self._max_tool_calls:
                return self._failed_response(
                    task_id,
                    task,
                    steps,
                    user,
                    request,
                    "工具调用次数超限，请缩小任务范围后重试。",
                    metadata={"max_tool_calls": self._max_tool_calls},
                )
            step = pending_steps.pop(0)
            selected_tool = step.tool_name
            params = self._resolve_tool_params(step.arguments, raw_observations)
            spec = self._registry.get(selected_tool)
            tool_call_count += 1
            try:
                execution = await asyncio.wait_for(
                    self._registry.execute(selected_tool, params, workspace, user),
                    timeout=self._remaining_seconds(started_at),
                )
            except TimeoutError:
                return self._runtime_timeout_response(
                    task_id, task, steps, user, request,
                    phase="tool", tool_name=selected_tool,
                )
            call_status = (
                "needs_clarification"
                if execution.status == "needs_clarification"
                else ("failed" if execution.status == "failed" else "success")
            )
            steps.append(
                AgentStep(
                    type="action",
                    phase="call",
                    title="调用工具",
                    content=f"调用 {selected_tool}",
                    tool_name=selected_tool,
                    input_json=params,
                    output_json=execution.output,
                    status=call_status,
                    error_message=execution.error_message,
                    metadata={"latency_ms": execution.latency_ms},
                )
            )

            if execution.status == "needs_clarification":
                final_answer = execution.clarification or (spec.clarification if spec else "请补充必要信息。")
                steps.append(
                    AgentStep(
                        type="answer",
                        phase="answer",
                        title="需要补充信息",
                        content=final_answer,
                        tool_name=selected_tool,
                        status="needs_clarification",
                        error_message=final_answer,
                        metadata={"expected_fields": list((spec.definition.input_schema.get("required", []) if spec else []))},
                    )
                )
                response = AgentTaskResponse(
                    id=task_id,
                    task=task,
                    status="needs_clarification",
                    steps=steps,
                    final_answer=final_answer,
                    result_view={"type": "text", "content": final_answer, "tools": self._planned_tool_names(plan.plan_steps)},
                )
                self._save(response, user, request)
                return response

            if execution.status == "failed":
                final_answer = execution.error_message or "工具调用失败，请修改参数后重试。"
                steps.append(
                    AgentStep(
                        type="observation",
                        phase="observe",
                        title="工具失败",
                        content=final_answer,
                        tool_name=selected_tool,
                        status="failed",
                        error_message=final_answer,
                    )
                )
                raw_observations.append(
                    {"tool": selected_tool, "status": "failed", "input": params, "error": final_answer}
                )
                retry_counts[selected_tool] = retry_counts.get(selected_tool, 0) + 1
                if retry_counts[selected_tool] <= self._max_retries_per_tool:
                    try:
                        revision = await asyncio.wait_for(
                            self._revise_plan(
                                task,
                                context_file_ids,
                                kb_id,
                                request["inputs"],
                                plan,
                                raw_observations,
                                f"{selected_tool} 调用失败：{final_answer}",
                                steps,
                            ),
                            timeout=self._remaining_seconds(started_at),
                        )
                    except TimeoutError:
                        return self._runtime_timeout_response(
                            task_id, task, steps, user, request,
                            phase="revision", tool_name=selected_tool,
                        )
                    if revision.plan_steps:
                        pending_steps = [*revision.plan_steps, *pending_steps]
                        continue
                return self._failed_response(
                    task_id,
                    task,
                    steps,
                    user,
                    request,
                    final_answer,
                    result_view={"type": "text", "content": final_answer, "tools": self._planned_tool_names(plan.plan_steps)},
                )

            observe_content = self._format_observation(selected_tool, execution.output)
            tool_answer = self._format_final_answer(selected_tool, execution.output)
            observations.append((selected_tool, execution.output, observe_content, tool_answer))
            raw_observations.append(
                {"tool": selected_tool, "status": "success", "input": params, "output": execution.output}
            )
            steps.append(
                AgentStep(
                    type="observation",
                    phase="observe",
                    title="观察结果",
                    content=observe_content,
                    tool_name=selected_tool,
                    output_json=execution.output,
                )
            )
            if self._is_empty_tool_result(selected_tool, execution.output):
                try:
                    revision = await asyncio.wait_for(
                        self._revise_plan(
                            task,
                            context_file_ids,
                            kb_id,
                            request["inputs"],
                            plan,
                            raw_observations,
                            f"{selected_tool} 未查询到结果",
                            steps,
                        ),
                        timeout=self._remaining_seconds(started_at),
                    )
                except TimeoutError:
                    return self._runtime_timeout_response(
                        task_id, task, steps, user, request,
                        phase="revision", tool_name=selected_tool,
                    )
                if revision.plan_steps:
                    pending_steps = [*revision.plan_steps, *pending_steps]

        final_answer = self._combine_final_answers(observations)
        answer_tool = observations[0][0] if len(observations) == 1 else None
        steps.append(
            AgentStep(
                type="answer",
                phase="answer",
                title="最终回答",
                content=final_answer,
                tool_name=answer_tool,
                output_json={"answer": final_answer},
            )
        )
        response = AgentTaskResponse(
            id=task_id,
            task=task,
            status="completed",
            steps=steps,
            final_answer=final_answer,
            result_view=self._combined_result_view(observations, final_answer),
        )
        self._save(response, user, request)
        return response

    async def preview_plan(
        self,
        payload: Any,
        user: UserPublic,
        *,
        inputs: dict[str, Any] | None = None,
    ) -> AgentPlanPreviewResponse:
        del user
        task = getattr(payload, "task", "")
        context_file_ids = list(getattr(payload, "context_file_ids", []) or [])
        kb_id = getattr(payload, "kb_id", None)
        plan = await self._planner.plan(task, context_file_ids, kb_id, inputs or {})
        preview_steps = []
        for step in plan.plan_steps:
            risk_level, risk_reason = self._tool_risk(step.tool_name)
            preview_steps.append(AgentPlanPreviewStep(
                tool_name=step.tool_name,
                arguments=step.arguments,
                rationale=step.rationale,
                risk_level=risk_level,
                risk_reason=risk_reason,
            ))
        risk_level, risk_reason = self._plan_risk(preview_steps)
        return AgentPlanPreviewResponse(
            intent=plan.intent,
            missing_fields=plan.missing_fields,
            answer_strategy=plan.answer_strategy,
            risk_level=risk_level,
            risk_reason=risk_reason,
            requires_confirmation=risk_level in {"medium", "high"},
            steps=preview_steps,
        )

    def get(self, task_id: str, user: UserPublic) -> AgentTaskResponse | None:
        if _AGENT_OWNERS.get(task_id) != user.id:
            return None
        return _AGENT_TASKS.get(task_id)

    def delete(self, task_id: str, user: UserPublic) -> None:
        if _AGENT_OWNERS.get(task_id) != user.id:
            return
        _AGENT_TASKS.pop(task_id, None)
        _AGENT_OWNERS.pop(task_id, None)
        _AGENT_REQUESTS.pop(task_id, None)

    async def continue_task(
        self,
        task_id: str,
        inputs: dict[str, Any],
        workspace: Any,
        user: UserPublic,
    ) -> AgentTaskResponse | None:
        if _AGENT_OWNERS.get(task_id) != user.id:
            return None
        request = _AGENT_REQUESTS.get(task_id)
        if not request:
            return None
        payload = type(
            "_AgentPayload",
            (),
            {
                "task": request["task"],
                "context_file_ids": request.get("context_file_ids", []),
                "kb_id": request.get("kb_id"),
            },
        )()
        merged_inputs = {**request.get("inputs", {}), **inputs}
        return await self.run(payload, workspace, user, task_id=task_id, continuation_inputs=merged_inputs)

    def _save(self, response: AgentTaskResponse, user: UserPublic, request: dict[str, Any]) -> None:
        _AGENT_TASKS[response.id] = response
        _AGENT_OWNERS[response.id] = user.id
        _AGENT_REQUESTS[response.id] = request

    def _plan_tool(
        self,
        task: str,
        context_file_ids: list[str],
        kb_id: str | None,
        inputs: dict[str, Any],
    ) -> tuple[str | None, dict[str, Any]]:
        planned = self._planned_tools(self._planner.fallback_plan(task, context_file_ids, kb_id, inputs))
        return planned[0] if planned else (None, {})

    def _plan_tools(
        self,
        task: str,
        context_file_ids: list[str],
        kb_id: str | None,
        inputs: dict[str, Any],
    ) -> list[tuple[str, dict[str, Any]]]:
        return self._planned_tools(self._planner.fallback_plan(task, context_file_ids, kb_id, inputs))

    def _planned_tools(self, plan: AgentPlan) -> list[tuple[str, dict[str, Any]]]:
        return [(step.tool_name, step.arguments) for step in plan.plan_steps]

    def _direct_answer(self, task: str, inputs: dict[str, Any]) -> str:
        history = inputs.get("_history") if isinstance(inputs, dict) else None
        if isinstance(history, list) and history:
            previous = [
                str(item.get("content", "")).strip()
                for item in history[-4:]
                if isinstance(item, dict) and str(item.get("content", "")).strip()
            ]
            context = "；".join(previous)
            return f"基于前文继续回答：{task}" + (f"\n\n前文要点：{context}" if context else "")
        return f"这是一个可直接回答的问题：{task}"

    def _plan_label(self, steps: list[PlannedToolCall]) -> str:
        return " -> ".join(step.tool_name for step in steps) if steps else "direct_answer"

    def _plan_input_json(self, plan: AgentPlan) -> dict[str, Any]:
        return {
            "intent": plan.intent,
            "missing_fields": plan.missing_fields,
            "answer_strategy": plan.answer_strategy,
            "steps": [
                {
                    "tool": step.tool_name,
                    "input": step.arguments,
                    "rationale": step.rationale,
                }
                for step in plan.plan_steps
            ],
        }

    def _planned_tool_names(self, steps: list[PlannedToolCall]) -> list[str]:
        return [step.tool_name for step in steps]

    async def _revise_plan(
        self,
        task: str,
        context_file_ids: list[str],
        kb_id: str | None,
        inputs: dict[str, Any],
        previous_plan: AgentPlan,
        observations: list[dict[str, Any]],
        reason: str,
        steps: list[AgentStep],
    ) -> AgentPlan:
        revision = await self._planner.revise(
            task,
            context_file_ids,
            kb_id,
            inputs,
            previous_plan=previous_plan,
            observations=observations,
            reason=reason,
        )
        if revision.plan_steps:
            steps.append(
                AgentStep(
                    type="thought",
                    phase="plan",
                    title="修正规划",
                    content=f"根据观察调整工具：{self._plan_label(revision.plan_steps)}",
                    tool_name=revision.plan_steps[0].tool_name if len(revision.plan_steps) == 1 else None,
                    input_json=self._plan_input_json(revision),
                    metadata={"revision_reason": reason},
                )
            )
        return revision

    def _failed_response(
        self,
        task_id: str,
        task: str,
        steps: list[AgentStep],
        user: UserPublic,
        request: dict[str, Any],
        final_answer: str,
        *,
        result_view: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentTaskResponse:
        steps.append(
            AgentStep(
                type="answer",
                phase="answer",
                title="执行失败",
                content=final_answer,
                status="failed",
                error_message=final_answer,
                metadata=metadata or {},
            )
        )
        response = AgentTaskResponse(
            id=task_id,
            task=task,
            status="failed",
            steps=steps,
            final_answer=final_answer,
            result_view=result_view or {"type": "text", "content": final_answer},
        )
        self._save(response, user, request)
        return response

    def _remaining_seconds(self, started_at: float) -> float:
        remaining = self._max_runtime_seconds - (time.monotonic() - started_at)
        if remaining <= 0:
            raise TimeoutError
        return remaining

    def _runtime_timeout_response(
        self,
        task_id: str,
        task: str,
        steps: list[AgentStep],
        user: UserPublic,
        request: dict[str, Any],
        *,
        phase: str,
        tool_name: str | None = None,
    ) -> AgentTaskResponse:
        if phase == "plan":
            message = "智能体任务规划超时，请稍后重试。"
        elif phase == "revision":
            message = f"工具 {tool_name} 执行后的计划修正超时，请稍后重试。"
        else:
            message = f"工具 {tool_name} 执行超时，请稍后重试或缩小任务范围。"
        return self._failed_response(
            task_id,
            task,
            steps,
            user,
            request,
            message,
            metadata={
                "max_runtime_seconds": self._max_runtime_seconds,
                "timeout_phase": phase,
                "tool_name": tool_name,
            },
        )

    def _format_observation(self, tool_name: str, output: dict[str, Any]) -> str:
        if tool_name == "calculator":
            return f"计算结果：{output['result']}"
        if tool_name == "course_lookup":
            courses = output.get("courses", [])
            if not courses:
                return "没有查询到课程。"
            return "\n".join(f"{course['name']}（{course['code']}，{course['teacher']}）" for course in courses)
        if tool_name == "file_content_search":
            matches = output.get("matches", [])
            if not matches:
                return "没有查询到匹配文件内容。"
            return "\n".join(f"{match['file_name']}: {match['snippet']}" for match in matches)
        if tool_name == "python_data":
            return f"数据行数：{output.get('row_count', 0)}，列：{', '.join(output.get('columns', []))}"
        if tool_name == "rag_query":
            return f"知识库回答：{output.get('answer', '')}"
        if tool_name == "file_metadata_query":
            return f"查询到 {output.get('total', 0)} 个文件。"
        if tool_name == "database_query":
            return f"查询表 {output.get('table', '')}，返回 {len(output.get('rows', []))} 行。"
        if tool_name == "weather_lookup":
            return f"天气服务返回：{output.get('provider_response', {})}"
        if tool_name == "kb_interest_extract":
            return f"提取到兴趣关键词：{', '.join(output.get('interests', []))}"
        if tool_name == "arxiv_search":
            return f"从 arXiv 查询到 {len(output.get('papers', []))} 篇相关论文。"
        if tool_name == "arxiv_markdown_render":
            return f"已生成 Markdown 报告，包含 {output.get('paper_count', 0)} 篇论文。"
        if tool_name == "knowledge_markdown_write":
            return f"已写入知识库文档：{output.get('file_name', '')}。"
        return str(output)

    def _resolve_tool_params(self, value: Any, observations: list[dict[str, Any]]) -> Any:
        if isinstance(value, str):
            return self._resolve_reference(value, observations)
        if isinstance(value, list):
            return [self._resolve_tool_params(item, observations) for item in value]
        if isinstance(value, dict):
            return {key: self._resolve_tool_params(item, observations) for key, item in value.items()}
        return value

    def _resolve_reference(self, value: str, observations: list[dict[str, Any]]) -> Any:
        if not value.startswith("$"):
            return value
        # Normalize ${tool.field}, $(tool.field), <tool.field> → tool.field
        ref = value[1:].strip("{}()<> ")
        path = ref.split(".")
        if len(path) < 2:
            return value
        tool_name = path[0]
        selected = next(
            (
                item.get("output", {})
                for item in reversed(observations)
                if item.get("tool") == tool_name and item.get("status") == "success"
            ),
            None,
        )
        # Fallback: if tool_name looks like "stepN", try by observation index
        if selected is None and tool_name.startswith("step") and tool_name[4:].isdigit():
            idx = int(tool_name[4:]) - 1  # 1-indexed → 0-indexed
            if 0 <= idx < len(observations):
                obs = observations[idx]
                if obs.get("status") == "success":
                    selected = obs.get("output", {})
        if selected is None:
            return value
        current: Any = selected
        for part in path[1:]:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                current = current[int(part)]
            else:
                return value
            if current is None:
                return value
        return current

    def _format_final_answer(self, tool_name: str, output: dict[str, Any]) -> str:
        if tool_name == "calculator":
            return f"计算结果是 {output['result']}。"
        if tool_name == "course_lookup":
            courses = output.get("courses", [])
            if not courses:
                return "没有查询到相关课程，请换一个课程名称或关键词。"
            return "查询到课程：" + "；".join(
                f"{course['name']}（{course['code']}，{course['teacher']}，{course['credits']} 学分）"
                for course in courses
            )
        if tool_name == "file_content_search":
            matches = output.get("matches", [])
            if not matches:
                return "没有在文件内容中查询到匹配结果。"
            return "文件内容查询结果：" + "；".join(
                f"{match['file_name']}：{match['snippet']}" for match in matches
            )
        if tool_name == "python_data":
            return f"数据文件包含 {output.get('row_count', 0)} 行，字段包括：{', '.join(output.get('columns', []))}。"
        if tool_name == "rag_query":
            answer = str(output.get("answer", "")).strip()
            citations = output.get("citations", [])
            suffix = f"（引用 {len(citations)} 条）" if citations else ""
            return f"{answer}{suffix}" if answer else "知识库未返回答案。"
        if tool_name == "file_metadata_query":
            files = output.get("files", [])
            if not files:
                return "没有查询到符合条件的文件。"
            return "查询到文件：" + "；".join(
                f"{file.get('name')}（{file.get('type')}，{file.get('parse_status')}）"
                for file in files
            )
        if tool_name == "database_query":
            rows = output.get("rows", [])
            return f"受限数据表 {output.get('table')} 返回 {len(rows)} 行记录。"
        if tool_name == "weather_lookup":
            return f"{output.get('location')} 天气查询已返回真实服务结果。"
        if tool_name == "kb_interest_extract":
            return f"已从知识库提取兴趣关键词：{', '.join(output.get('interests', []))}。"
        if tool_name == "arxiv_search":
            papers = output.get("papers", [])
            interests = output.get("interests", [])
            return f"已根据兴趣（{', '.join(interests)}）检索 arXiv，返回 {len(papers)} 篇论文。"
        if tool_name == "arxiv_markdown_render":
            return f"已整理 Markdown 报告，包含 {output.get('paper_count', 0)} 篇论文。"
        if tool_name == "knowledge_markdown_write":
            return f"已将 Markdown 报告写入知识库，文件：{output.get('file_name')}，文档 ID：{output.get('document_id')}。"
        return str(output)

    def _result_view(self, tool_name: str, output: dict[str, Any], final_answer: str) -> dict[str, Any]:
        if tool_name == "course_lookup":
            return {"type": "table", "columns": ["code", "name", "teacher", "credits"], "rows": output.get("courses", [])}
        if tool_name == "file_content_search":
            return {"type": "table", "columns": ["file_name", "snippet"], "rows": output.get("matches", [])}
        if tool_name == "python_data":
            return {
                "type": "chart",
                "content": final_answer,
                "chart": {"kind": "bar", "series": output.get("numeric_summary", {})},
                "key_results": [f"行数：{output.get('row_count', 0)}"],
            }
        if tool_name == "rag_query":
            return {
                "type": "text",
                "content": final_answer,
                "citations": output.get("citations", []),
                "key_results": [output.get("answer", "")],
            }
        if tool_name == "file_metadata_query":
            return {
                "type": "table",
                "columns": ["name", "type", "parse_status", "size", "updated_at"],
                "rows": output.get("files", []),
            }
        if tool_name == "database_query":
            return {
                "type": "table",
                "columns": output.get("columns", []),
                "rows": output.get("rows", []),
            }
        if tool_name == "weather_lookup":
            return {"type": "text", "content": final_answer, "raw": output.get("provider_response", {})}
        if tool_name == "kb_interest_extract":
            return {
                "type": "table",
                "content": final_answer,
                "columns": ["file_name", "summary"],
                "rows": output.get("documents", []),
                "key_results": output.get("interests", []),
            }
        if tool_name == "arxiv_search":
            return {
                "type": "table",
                "content": final_answer,
                "columns": ["title", "published", "categories", "link"],
                "rows": output.get("papers", []),
                "key_results": output.get("interests", []),
            }
        if tool_name == "arxiv_markdown_render":
            return {"type": "text", "content": output.get("markdown", final_answer)}
        if tool_name == "knowledge_markdown_write":
            return {
                "type": "text",
                "content": final_answer,
                "key_results": [
                    f"报告文件：{output.get('file_name')}",
                    f"知识库文档：{output.get('document_id')}",
                ],
            }
        return {"type": "text", "content": final_answer}

    def _combine_final_answers(self, observations: list[tuple[str, dict[str, Any], str, str]]) -> str:
        if len(observations) == 1:
            return observations[0][3]
        return "已完成多步骤任务：" + "；".join(answer for _, _, _, answer in observations)

    def _combined_result_view(self, observations: list[tuple[str, dict[str, Any], str, str]], final_answer: str) -> dict[str, Any]:
        if len(observations) == 1:
            tool_name, output, _, _ = observations[0]
            return self._result_view(tool_name, output, final_answer)
        return {
            "type": "mixed",
            "content": final_answer,
            "tools": [tool_name for tool_name, _, _, _ in observations],
            "key_results": [answer for _, _, _, answer in observations],
            "sections": [
                {
                    "tool": tool_name,
                    "observation": observation,
                    "result": output,
                }
                for tool_name, output, observation, _ in observations
            ],
        }

    def _is_empty_tool_result(self, tool_name: str, output: dict[str, Any]) -> bool:
        if tool_name == "course_lookup":
            return output.get("courses") == []
        if tool_name == "file_content_search":
            return output.get("matches") == []
        if tool_name == "file_metadata_query":
            return output.get("files") == []
        if tool_name == "database_query":
            return output.get("rows") == []
        if tool_name == "rag_query":
            return bool(output.get("error_code"))
        return False

    def _tool_risk(self, tool_name: str) -> tuple[str, str]:
        if tool_name in {"database_query", "weather_lookup", "arxiv_search"}:
            return "high", "将访问受限系统数据或外部服务，执行前需要确认。"
        if tool_name in {"rag_query", "file_content_search", "python_data", "file_metadata_query", "kb_interest_extract", "knowledge_markdown_write"}:
            return "medium", "将读取用户可访问的文件或知识库内容，执行前建议确认。"
        return "low", "仅使用本地低风险工具。"

    def _plan_risk(self, steps: list[AgentPlanPreviewStep]) -> tuple[str, str]:
        if not steps:
            return "low", "无需调用工具。"
        if any(step.risk_level == "high" for step in steps):
            reasons = [step.risk_reason for step in steps if step.risk_level == "high"]
            return "high", reasons[0]
        if any(step.risk_level == "medium" for step in steps):
            reasons = [step.risk_reason for step in steps if step.risk_level == "medium"]
            return "medium", reasons[0]
        return "low", "仅使用低风险工具。"


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
