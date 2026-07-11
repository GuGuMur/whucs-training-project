# Production LLM Agent Tool-Flow Implementation Plan

## Goal
Upgrade the current non-mock MVP tool-flow into a genuinely usable LLM-driven agent system. The target is an agent that can understand natural language, ask clarifying questions, generate structured tool calls through an LLM, execute tools safely, observe results, revise plans, and present transparent final answers in the Web UI.

## Current Baseline
- V2 tool-flow is real but still MVP: deterministic planner, DB-persisted tasks/steps, registered tools, file search, calculator, course JSON lookup, CSV analysis, mixed/chart UI, and 10-case system evaluation.
- RAG answer generation already has an OpenAI-compatible LLM service with template fallback.
- Agent planning and tool selection are not yet LLM tool-calling based.
- Existing registered tools are useful for demonstration, but most are local-only and limited.

## Target Architecture

### Backend Services
- `AgentPlanner`: builds a system prompt, available tool schema list, conversation/task context, and asks an LLM for a structured plan.
- `ToolCallingLLM`: OpenAI-compatible wrapper for structured JSON/tool-call output. It must support timeout, retry, fallback, and deterministic tests.
- `AgentExecutor`: runs an iterative loop: understand -> plan -> call -> observe -> revise -> answer.
- `ToolRegistry`: remains the single source of tool definitions and runtime handlers.
- `AgentMemory`: persists task, turns, messages, plan revisions, tool calls, observations, errors, and final answer.
- `AgentPolicy`: enforces max steps, max runtime, allowed tools, file/team permissions, and user-visible refusal/error messages.

### Data Model
- Extend current `agent_tasks` and `agent_task_steps`.
- Add `agent_messages`: task id, role, content, structured metadata, created_at.
- Add `agent_tool_calls`: task id, step id, tool name, input JSON, output JSON, status, error, latency, created_at.
- Add optional `agent_plan_revisions`: task id, revision number, plan JSON, reason, created_at.

### API Surface
- `POST /api/v2/agents/tasks`: create and run or start streaming task.
- `GET /api/v2/agents/tasks`: list user's task history.
- `GET /api/v2/agents/tasks/{task_id}`: detail with messages, steps, tool calls, result view.
- `POST /api/v2/agents/tasks/{task_id}/continue`: continue after clarification or user follow-up.
- `POST /api/v2/agents/tasks/{task_id}/cancel`: cancel running task.
- Optional streaming: `POST /api/v2/agents/tasks/stream` using SSE for tokens/steps/tool events.

## Phase 32: LLM Tool-Calling Contract
- [x] Define strict JSON schema for LLM planner output: intent, missing_fields, plan_steps, selected_tools, arguments, answer_strategy.
- [x] Implement `ToolCallingLLM` around the existing OpenAI-compatible config (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`).
- [x] Add deterministic fallback planner for CI and no-key local runs.
- [x] Add tests for valid plan parsing, invalid JSON repair, missing field clarification, and no-key fallback.
- [x] Ensure no raw chain-of-thought is stored or shown; only concise plan summaries and tool rationale are persisted.

## Phase 33: Iterative Agent Loop
- [x] Refactor `AgentExecutor` from one-pass execution to a bounded loop.
- [x] Loop rules: max 6 tool calls, max 2 retries per failed tool, max wall time.
- [x] Support plan revision: when a tool fails or returns no result, LLM receives observation and can adjust next step.
- [x] Persist each plan revision, tool call, observation, and final answer through existing agent step persistence.
- [x] Preserve existing deterministic tests while adding LLM-planner mocked tests.
- [x] Add API-level cancel support.

## Phase 34: Real Tool Expansion
- [x] Keep existing `calculator`, `file_content_search`, `python_data`, and `course_lookup`.
- [x] Add `rag_query`: query selected knowledge base through `RagPipeline`, with citations.
- [x] Add `database_query`: restricted read-only whitelisted tables only; no arbitrary destructive SQL.
- [x] Add `weather_lookup`: external API only when configured; returns a clear configuration error instead of mock weather when not configured.
- [x] Add `file_metadata_query`: query user/team accessible files by name, tag, type, parse status, updated time.
- [x] Each tool declares input schema, output schema, and result-view mapping.

## Phase 35: Agent Memory And Multi-Turn Conversation
- [x] Store user/assistant messages per task.
- [x] Continue tasks with user follow-up questions while retaining prior tool observations.
- [x] Support explicit "new task" versus "continue this task".
- [x] Summarize long histories before sending to LLM.
- [x] Show prior tool calls and relevant citations in task detail.

## Phase 36: Web UI Upgrade
- [x] Add task history list, active task detail, and continue/cancel controls.
- [x] Show LLM-generated plan as editable/confirmable when risk is medium or high.
- [x] Display tool call cards: tool, arguments, status, latency, output summary, error/retry.
- [x] Add streaming UI for plan events, tool events, and final answer tokens if SSE is implemented.
- [x] Add clear empty/error states for missing input, missing API key, no result, permission denied, and tool timeout.

## Phase 37: Security And Operations
- [x] Enforce per-user/team file and KB access before every tool call.
- [x] Add tool allowlist by user role and workflow context.
- [x] Add audit logs for agent task creation, tool execution, permission denial, cancellation, and final answer.
- [x] Add secret/config validation for external tools.
- [x] Add structured logging for latency, tool failure rate, and LLM retry count.

## Phase 38: Evaluation And Acceptance
- [x] Expand system evaluation from 10 cases to at least 25 cases.
- [x] Include direct answer, RAG, file search, database query, weather, CSV analysis, multi-tool, multi-turn, clarification, retry, no-result, permission denied, and invalid input.
- [x] Track task completion rate, tool selection accuracy, argument accuracy, grounded-answer citation rate, and average latency.
- [x] Add a report under `docs/superpowers/reports/` with success/failure examples and known limitations.
- [x] Acceptance target: >= 85% completion, >= 85% correct tool selection, no unauthorized data exposure in tests.

## Implementation Order
1. Add LLM planner contract and tests with mocked LLM outputs.
2. Refactor executor into iterative loop while preserving existing deterministic fallback behavior.
3. Add persistence for messages/tool calls/plan revisions.
4. Add `rag_query`, `file_metadata_query`, and one external/configured tool.
5. Upgrade frontend task history and execution trace UI.
6. Add security/audit hardening.
7. Expand system evaluation and report.

## Configuration Requirements
- Required for real LLM planning: `LLM_API_KEY`.
- Optional: `LLM_BASE_URL`, `LLM_MODEL`, `LLM_PROVIDER`.
- Optional for external weather: weather API key or configured provider.
- CI must pass without external API keys using mocked LLM and deterministic fallback.

## Verification Commands
- `cd backend && PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "agent or tool or workflow"`
- `cd backend && PYTHONPATH=. uv run python -m pytest tests/test_llm.py -q`
- `cd backend && PYTHONPATH=. uv run python -m pytest -q`
- `cd frontend && pnpm vitest run src/stores/__tests__/agent.spec.ts src/components/workflow/__tests__`
- `cd frontend && pnpm type-check`
- `cd frontend && pnpm build`
- `python3 -m json.tool .wolf/buglog.json >/dev/null`
- `git diff --check`
