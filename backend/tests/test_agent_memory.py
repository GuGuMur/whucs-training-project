from __future__ import annotations

from app.domain.workflow import AgentStep, AgentTaskContinueRequest, AgentTaskResponse
from app.services.workspace_db import WorkspaceServiceDB
from app.domain.schemas import UserPublic


def _response() -> AgentTaskResponse:
    return AgentTaskResponse(
        id="agent-memory-1",
        task="继续查询课程",
        status="completed",
        steps=[
            AgentStep(
                type="thought",
                phase="plan",
                title="任务规划",
                content="调用课程查询工具",
                input_json={"plan_steps": [{"tool_name": "course_lookup"}]},
            ),
            AgentStep(
                type="action",
                phase="call",
                title="调用 course_lookup",
                content="查询课程",
                tool_name="course_lookup",
                input_json={"query": "高等数学"},
                output_json={"courses": [{"name": "高等数学"}]},
                metadata={"latency_ms": 12},
            ),
            AgentStep(
                type="answer",
                phase="answer",
                title="最终回答",
                content="高等数学周一上课。",
            ),
        ],
        final_answer="高等数学周一上课。",
        result_view={"type": "table", "columns": ["name"], "rows": [["高等数学"]]},
    )


def test_agent_memory_preserves_history_and_appends_current_turn() -> None:
    service = WorkspaceServiceDB.__new__(WorkspaceServiceDB)
    messages = service._agent_messages_from_response(
        _response(),
        {
            "task": "继续查询课程",
            "context_file_ids": ["file-1"],
            "kb_id": "kb-1",
            "inputs": {
                "query": "高等数学",
                "_history": [{"role": "user", "content": "旧问题"}],
                "_history_summary": "旧摘要",
                "_prior_tool_calls": [{"tool_name": "course_lookup"}],
            },
            "history": [
                {"role": "user", "content": "课程安排是什么？", "metadata": {"source": "test"}},
                {"role": "assistant", "content": "请补充课程名称。", "metadata": {"status": "needs_clarification"}},
            ],
        },
    )

    assert [message.role for message in messages] == ["user", "assistant", "user", "assistant"]
    assert [message.content for message in messages] == [
        "课程安排是什么？",
        "请补充课程名称。",
        "继续查询课程",
        "高等数学周一上课。",
    ]
    assert '"_history"' not in messages[2].metadata_json
    assert '"_history_summary"' not in messages[2].metadata_json
    assert '"_prior_tool_calls"' not in messages[2].metadata_json
    assert messages[2].sequence == 2


def test_agent_memory_records_tool_calls_and_plan_revisions() -> None:
    service = WorkspaceServiceDB.__new__(WorkspaceServiceDB)
    response = _response()

    calls = service._agent_tool_calls_from_response(response)
    revisions = service._agent_plan_revisions_from_response(response)

    assert len(calls) == 1
    assert calls[0].tool_name == "course_lookup"
    assert calls[0].input_json == '{"query": "高等数学"}'
    assert calls[0].output_json == '{"courses": [{"name": "高等数学"}]}'
    assert calls[0].latency_ms == 12
    assert len(revisions) == 1
    assert revisions[0].revision_no == 0
    assert revisions[0].reason == "任务规划"
    assert '"course_lookup"' in revisions[0].plan_json


def test_agent_continue_request_accepts_follow_up_message() -> None:
    payload = AgentTaskContinueRequest(message="再查一下考试时间", inputs={"course_name": "高等数学"})

    assert payload.message == "再查一下考试时间"
    assert payload.inputs["course_name"] == "高等数学"


def test_agent_history_summary_is_bounded() -> None:
    service = WorkspaceServiceDB.__new__(WorkspaceServiceDB)
    history = [{"role": "user", "content": f"第 {index} 轮问题\n包含换行"} for index in range(30)]

    summary = service._summarize_agent_history(history)

    assert "第 10 轮问题 包含换行" in summary
    assert "第 29 轮问题 包含换行" in summary
    assert "第 0 轮问题" not in summary


def test_agent_task_stream_emits_steps_and_done() -> None:
    class _StreamService:
        async def create_agent_task(self, _payload, _user):
            return _response()

    service = _StreamService()
    service.stream_agent_task = WorkspaceServiceDB.stream_agent_task.__get__(service, _StreamService)
    user = UserPublic(id=1, username="stream-user", email="stream@example.com", display_name="Stream", roles=["user"])

    async def collect():
        return [event async for event in service.stream_agent_task(object(), user)]

    import asyncio
    events = asyncio.run(collect())

    assert any('"type": "plan"' in event for event in events)
    assert any('"type": "call"' in event for event in events)
    assert '"type": "done"' in events[-1]
