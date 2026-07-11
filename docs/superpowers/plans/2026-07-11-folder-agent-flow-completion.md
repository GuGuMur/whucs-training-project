# Personal Folder And Agent Tool-Flow Completion Plan

## Goal
Complete the personal-folder baseline and rebuild the tool-flow feature so it uses real project data, persists execution state, supports multi-step natural-language tasks, exposes transparent execution results in the Web UI, and has at least 10 system test cases with completion and tool-selection metrics.

## Current Findings
- Personal roots are partly implemented as `personal-root-{user.id}`, but `upload_file()` still stores the incoming `folder_id` instead of the resolved folder id, so omitted or legacy `personal-root` uploads can leak bad folder ids into file rows.
- Multipart upload completion is still placeholder-like: it returns a `FileItem` with `folder_id="personal-root"` and does not assemble persisted chunks into a real file.
- Folder create/update/delete APIs exist, and personal root rename/delete is blocked. The next slice should harden ownership tests, default-root behavior, rename/move/delete semantics, and frontend upload target handling.
- The current agent runtime has `ToolRegistry` and `AgentExecutor`, but only chooses one tool per request and stores tasks in process memory dictionaries.
- `course_lookup` currently uses an inline hardcoded catalog. That violates the new "no mock data" requirement; move it to a repository/data source and make the source explicit.
- The frontend already has `useAgentStore`, `AgentTaskComposer`, `ToolCatalogPanel`, `AgentExecutionTimeline`, and `ToolResultViewer`. These should be extended rather than replaced.

## Phase 29: Personal Folder Baseline Hardening
- [x] Add backend tests proving each new user gets a personal root folder in `/api/v2/folders/tree` and workspace/file-manager snapshots.
- [x] Normalize missing or legacy upload folder ids to `personal-root-{user.id}` before creating `File.folder_id`.
- [x] Complete multipart upload against real chunk/session data; assembled files must go through the same `upload_file()` path and resolved folder id.
- [x] Add tests for personal folder create, nested create, rename, move, delete, root rename rejection, root delete rejection, and file rehome behavior after folder delete.
- [x] Verify team folder uploads keep team scope/team id and personal uploads stay personal.
- [x] Update frontend file manager upload/create/rename/delete flows if any hardcoded `personal-root` remains.
- [ ] Regenerate OpenAPI client if contracts change and run backend/frontend focused checks.

## Phase 30: Tool-Flow Backend Rebuild
- [x] Replace process-memory agent task storage with DB models/repositories for `AgentTask` and `AgentStep`, including owner id, status, request payload, result view, and timestamps.
- [x] Add an explicit task-plan schema: understand result, ordered subtask list, selected tool name, generated arguments, retry/fallback policy, and final synthesis metadata.
- [x] Implement deterministic NLU planning for common Chinese task patterns, with optional LLM planner only as an enhancement when configured. The deterministic path must handle direct answer, calculator, course lookup, file content search, CSV/data analysis, and multi-tool requests.
- [x] Support multi-step execution: run multiple planned tool calls in order, append `understand -> plan -> call -> observe -> answer` steps for each relevant part, and synthesize a single final answer.
- [x] Implement clarification state for missing parameters, storing the blocked step and expected fields so `/continue` resumes the exact plan instead of re-planning from scratch.
- [x] Add retry/fallback behavior for failed or incomplete tool calls: fix invalid params when possible, switch to a compatible tool when appropriate, or return a clear guided error.
- [x] Remove or isolate legacy placeholder agent helpers in `WorkspaceServiceDB` so v2 tools come only from `ToolRegistry` and real data sources.

## Phase 31: Real Tool Sources And Result Views
- [x] Keep at least four tools: `calculator`, `course_lookup`, `file_content_search`, and `python_data`.
- [x] Calculator: continue using safe AST evaluation; add tests for invalid expressions and divide-by-zero messaging.
- [x] Course lookup: move catalog data out of inline code into a real repository/data file or DB seed with source metadata; return no-result guidance when no course matches.
- [x] File content search: use authenticated file access checks, durable file content, and optional selected file ids or knowledge-base context. Do not search another user's personal files.
- [x] Python data: parse uploaded CSV files, return row/column summary, numeric statistics, and a simple chart/table-compatible result view.
- [x] Define a stable `result_view` contract: `type` (`text`, `table`, `chart`, `mixed`), `content`, `columns`, `rows`, `chart`, `tools`, `key_results`.
- [x] Ensure every tool has a clear name, description, input schema, output schema, error schema, and frontend-visible category.

## Phase 32: Web UI Completion
- [ ] Extend `useAgentStore` to load task detail/history from persisted backend APIs and preserve active task after refresh.
- [ ] Update `AgentTaskComposer` so clarification input maps to backend-requested fields instead of sending broad aliases like `answer/course_name/query` for every continuation.
- [ ] Update `AgentExecutionTimeline` to show grouped multi-step plans, tool calls, retries, failures, and observations without nested card clutter.
- [ ] Update `ToolResultViewer` to render `text`, `table`, and simple `chart` result types, plus called tools, main steps, and key results.
- [ ] Keep `WorkflowBuilderView.vue` as a composition surface consuming stores/components; avoid direct `fetch()` or mock debug endpoints.
- [ ] Add frontend store/component tests for direct answer, single tool, multi-tool, clarification/resume, failed tool, table result, and chart result states.

## Phase 33: System Test And Metrics
- [x] Add at least 10 backend system cases covering direct answer, calculator, course lookup success, course no-result, file content search success, file no-result, CSV data analysis, multi-tool task, missing info clarification, continuation success, invalid parameters, and unauthorized file access.
- [x] For each case record expected status, expected tools, expected key result, and whether clarification is expected.
- [x] Add a metrics helper that reports task completion rate and tool-selection accuracy from the 10+ cases.
- [x] Document typical successes and failures in a short report under `docs/superpowers/reports/`.
- [x] Verification target: backend full suite, frontend full suite, type-check, build, JSON validation, and `git diff --check`.

## Suggested Implementation Order
1. Lock down folder behavior first because file tools and knowledge scopes depend on correct folder ownership.
2. Add backend agent persistence/schema tests before rewriting executor logic.
3. Refactor tools to real repositories/data sources and update registry contracts.
4. Extend executor to multi-step plans, clarification resume, and retry/fallback.
5. Regenerate the client and update Pinia/store/UI surfaces.
6. Add system metrics and final verification.

## Verification Commands
- `cd backend && PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "folder or multipart or agent or tool"`
- `cd backend && PYTHONPATH=. uv run python -m pytest -q`
- `cd frontend && pnpm generate:client`
- `cd frontend && pnpm vitest run src/stores/__tests__/agent.spec.ts src/components/workflow/__tests__`
- `cd frontend && pnpm type-check`
- `cd frontend && pnpm build`
- `python3 -m json.tool .wolf/buglog.json >/dev/null`
- `git diff --check`
