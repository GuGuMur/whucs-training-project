from __future__ import annotations

import re
import secrets
from typing import Any

from app.domain.schemas import AgentStep, AgentTaskResponse, UserPublic
from app.services.tool_registry import ToolRegistry


_AGENT_TASKS: dict[str, AgentTaskResponse] = {}
_AGENT_OWNERS: dict[str, int] = {}
_AGENT_REQUESTS: dict[str, dict[str, Any]] = {}


class AgentExecutor:
    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self._registry = registry or ToolRegistry()

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
        selected_tool, params = self._plan_tool(task, context_file_ids, kb_id, request["inputs"])
        task_id = task_id or f"agent-{secrets.token_hex(4)}"

        steps: list[AgentStep] = [
            AgentStep(
                type="thought",
                phase="understand",
                title="理解任务",
                content=f"识别用户任务：{task}",
            ),
            AgentStep(
                type="thought",
                phase="plan",
                title="规划步骤",
                content=f"选择工具：{selected_tool or 'direct_answer'}",
                tool_name=selected_tool,
                input_json=params,
            ),
        ]

        if selected_tool is None:
            final_answer = f"这是一个可直接回答的问题：{task}"
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

        spec = self._registry.get(selected_tool)
        execution = await self._registry.execute(selected_tool, params, workspace, user)
        steps.append(
            AgentStep(
                type="action",
                phase="call",
                title="调用工具",
                content=f"调用 {selected_tool}",
                tool_name=selected_tool,
                input_json=params,
                status="needs_clarification" if execution.status == "needs_clarification" else "success",
                error_message=execution.error_message,
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
                )
            )
            response = AgentTaskResponse(
                id=task_id,
                task=task,
                status="needs_clarification",
                steps=steps,
                final_answer=final_answer,
                result_view={"type": "text", "content": final_answer},
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
            response = AgentTaskResponse(
                id=task_id,
                task=task,
                status="failed",
                steps=steps,
                final_answer=final_answer,
                result_view={"type": "text", "content": final_answer},
            )
            self._save(response, user, request)
            return response

        observe_content = self._format_observation(selected_tool, execution.output)
        final_answer = self._format_final_answer(selected_tool, execution.output)
        steps.extend(
            [
                AgentStep(
                    type="observation",
                    phase="observe",
                    title="观察结果",
                    content=observe_content,
                    tool_name=selected_tool,
                    output_json=execution.output,
                ),
                AgentStep(
                    type="answer",
                    phase="answer",
                    title="最终回答",
                    content=final_answer,
                    tool_name=selected_tool,
                    output_json={"answer": final_answer},
                ),
            ]
        )
        response = AgentTaskResponse(
            id=task_id,
            task=task,
            status="completed",
            steps=steps,
            final_answer=final_answer,
            result_view=self._result_view(selected_tool, execution.output, final_answer),
        )
        self._save(response, user, request)
        return response

    def get(self, task_id: str, user: UserPublic) -> AgentTaskResponse | None:
        if _AGENT_OWNERS.get(task_id) != user.id:
            return None
        return _AGENT_TASKS.get(task_id)

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
        if "计算" in task or re.search(r"\d+\s*[-+*/]", task):
            return "calculator", {"expression": inputs.get("expression") or _extract_expression(task)}
        if "课程" in task:
            query = inputs.get("query") or _extract_course_query(task)
            return "course_lookup", {"query": query}
        if "文件" in task or context_file_ids:
            return "file_content_search", {
                "query": inputs.get("query") or _extract_search_query(task),
                "file_ids": inputs.get("file_ids") or context_file_ids,
                "kb_id": kb_id,
            }
        if "csv" in task.lower() or "数据" in task:
            return "python_data", {"file_id": inputs.get("file_id") or (context_file_ids[0] if context_file_ids else "")}
        return None, {}

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
        return str(output)

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
        return str(output)

    def _result_view(self, tool_name: str, output: dict[str, Any], final_answer: str) -> dict[str, Any]:
        if tool_name == "course_lookup":
            return {"type": "table", "columns": ["code", "name", "teacher", "credits"], "rows": output.get("courses", [])}
        if tool_name == "file_content_search":
            return {"type": "table", "columns": ["file_name", "snippet"], "rows": output.get("matches", [])}
        return {"type": "text", "content": final_answer}


def _extract_expression(task: str) -> str:
    match = re.search(r"计算\s*(.+)$", task)
    return match.group(1).strip() if match else task.strip()


def _extract_course_query(task: str) -> str:
    cleaned = task.replace("查询", "").replace("课程信息", "").replace("课程", "").strip()
    return "" if not cleaned else cleaned


def _extract_search_query(task: str) -> str:
    match = re.search(r"查询\s+(.+)$", task)
    return match.group(1).strip() if match else task.strip()
