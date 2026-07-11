# Task Plan: Intelligent File Workspace Platform

## Goal
Build a frontend-backend separated, well-structured intelligent file management and agent collaboration platform based on the documents under `report/`.

## Current Phase
Phase 33 — Iterative Agent Loop (next)

## Phases

### Phase 1: Requirements & Current-State Discovery
- [x] Read project operating instructions.
- [x] Read relevant `report/requirements` and `report/design` sections.
- [x] Inspect frontend and backend framework state.
- [x] Document findings in `findings.md`.
- **Status:** complete

### Phase 2: MVP Architecture Skeleton
- [x] Replace the placeholder backend entry point with a FastAPI application package.
- [x] Add typed domain schemas and service modules for files, knowledge/RAG, tools, workflows, teams, and audit state.
- [x] Expose report-aligned `/api/v1` endpoints with deterministic in-memory demo behavior.
- [x] Add backend tests before implementation for the first vertical slice.
- **Status:** complete

### Phase 3: Vue Workbench Shell
- [x] Replace the default Vue starter screen with an operational Chinese workbench.
- [x] Add API client/types that consume the backend MVP endpoints.
- [x] Add file, RAG, agent, workflow, team, and admin surfaces in a compact app layout.
- [x] Add focused frontend tests before implementation for critical rendered states.
- **Status:** complete

### Phase 4: Integration & Verification
- [x] Run backend tests.
- [x] Run frontend unit/type/build checks.
- [x] Start local dev servers if needed and inspect the rendered app.
- [x] Record all verification results in `progress.md`.
- **Status:** complete

### Phase 5: Completion Audit
- [x] Compare implementation against report MVP requirements.
- [x] List remaining gaps honestly.
- [x] Update OpenWolf memory/cerebrum and planning files.
- **Status:** complete

### Phase 6: OpenAPI Client Generation Boundary
- [x] Add a backend OpenAPI export module and contract test.
- [x] Add frontend `@hey-api/openapi-ts` config and package scripts.
- [x] Generate `src/client/generated/` from the exported FastAPI schema.
- [x] Route live workspace snapshot calls through the generated SDK while keeping auth/session management in `src/auth/`.
- [x] Enforce generated-client boundaries with frontend architecture tests.
- **Status:** complete

### Phase 7: Frontend Auth Session & Protected Routing
- [x] Add a generated-client-backed auth Pinia store for login, registration, and current-user restoration.
- [x] Add a report-aligned login/register view under `views/`.
- [x] Protect the workspace route with a return-based Vue Router guard while keeping `/login` guest-only.
- [x] Link workspace loading to the stored auth session token without moving auth state into `client/`.
- [x] Add focused auth store, login view, and router guard tests.
- **Status:** complete

### Phase 8: Refresh Session Boundary Hardening
- [x] Add backend contract coverage for refresh-token rotation and token-kind enforcement.
- [x] Add `POST /api/v1/auth/refresh` with generated OpenAPI schema support.
- [x] Add frontend auth-store refresh action through the generated SDK.
- [x] Regenerate the OpenAPI client and re-run backend/frontend verification.
- **Status:** complete

### Phase 9: User Profile Maintenance
- [x] Add backend TDD coverage for `PATCH /api/v1/users/me`.
- [x] Add `UserUpdate`, profile update service logic, email uniqueness checks, and audit logging.
- [x] Regenerate the OpenAPI client so frontend auth can use `updateMeApiV1UsersMePatch`.
- [x] Add generated-client-backed auth store profile update action.
- [x] Add protected `/profile` route and Naive UI profile page under `views/`.
- [x] Add focused store, router, and view tests plus full verification.
- **Status:** complete

### Phase 10: Local Development API Proxy
- [x] Add/verify architecture coverage for the Vite dev `/api` proxy.
- [x] Align `frontend/vite.config.ts` so same-origin `/api` requests target `http://127.0.0.1:8000`.
- [x] Re-run frontend unit tests, backend tests, OpenAPI generation, build, JSON validation, and diff whitespace checks.
- **Status:** complete

### Phase 11: Login Failure Lockout
- [x] Add backend TDD coverage for FR-U05 failed-login counting, temporary account lockout, successful-login reset, and audit events.
- [x] Implement in-memory login lockout policy in the auth service.
- [x] Document login 401/423 `ErrorResponse` responses in OpenAPI and regenerate the frontend client.
- [x] Map generated-client `ACCOUNT_LOCKED` errors to a clear Chinese login message in the auth store.
- [x] Re-run backend tests, frontend tests, OpenAPI generation, build, JSON validation, and diff whitespace checks.
- **Status:** complete

### Phase 12: File Download & Delete Actions
- [x] Add backend TDD coverage for uploaded-file download, delete, 404 repeat-delete behavior, and audit events.
- [x] Store in-memory uploaded file bytes and expose `GET /api/v1/files/{file_id}/download` plus `DELETE /api/v1/files/{file_id}`.
- [x] Regenerate the OpenAPI client so frontend code uses generated file download/delete SDK calls.
- [x] Add generated-client-backed workspace store file actions and Naive UI row controls in `FileWorkbench.vue`.
- [x] Re-run backend tests, frontend tests, OpenAPI generation, and production build.
- **Status:** complete

### Phase 13: File Search & Upload UI
- [x] Add frontend TDD coverage for generated-client-backed file listing/upload actions and FileWorkbench search/upload events.
- [x] Add `listWorkspaceFiles()` and `uploadWorkspaceFile()` adapters in `src/client/workspace.ts` using generated SDK functions.
- [x] Add Pinia workspace state for active file filters, list loading, upload loading, and snapshot updates after search/upload.
- [x] Add a Naive UI + UnoCSS file search toolbar and upload panel while keeping page orchestration in `WorkspaceView.vue`.
- [x] Re-run focused frontend tests, all frontend tests, type checking, and production build.
- **Status:** complete

### Phase 14: Folder CRUD Tree & Breadcrumb UI
- [x] Add backend TDD coverage for FR-F02 folder create, nested tree, move, delete, non-empty delete rejection, root protection, and cycle prevention.
- [x] Expose `GET /folders/tree`, `POST /folders`, `PATCH /folders/{folder_id}`, and `DELETE /folders/{folder_id}` in the FastAPI/OpenAPI contract.
- [x] Regenerate the OpenAPI client so frontend code uses generated folder SDK calls through `src/client/workspace.ts`.
- [x] Add Pinia workspace folder tree state/actions, dynamic upload folder options, and active folder selection.
- [x] Add a Naive UI + UnoCSS folder tree/breadcrumb panel and wire it through `FileWorkbench.vue` and `WorkspaceView.vue`.
- [x] Re-run backend tests, frontend tests, type checking, OpenAPI generation, production build, JSON validation, and diff whitespace checks.
- **Status:** complete

### Phase 15: File Lifecycle Move Copy & Version UI
- [x] Add backend TDD coverage for FR-F01/FR-F05 file rename, move, tag update, copy, same-name upload versioning, version list, version restore, folder validation, and audit events.
- [x] Expose `PATCH /files/{file_id}`, `POST /files/{file_id}/copy`, `GET /files/{file_id}/versions`, and `POST /files/{file_id}/versions/{version_id}/restore` in the FastAPI/OpenAPI contract.
- [x] Regenerate the OpenAPI client so frontend code uses generated file lifecycle SDK calls through `src/client/workspace.ts`.
- [x] Add Pinia workspace file lifecycle state/actions for update, copy, version loading, and restore while keeping auth/session ownership in `auth/`.
- [x] Add a Naive UI + UnoCSS file lifecycle/detail panel inside the workbench for rename, move, tags, copy target, and version rollback.
- [x] Re-run backend tests, frontend focused/all tests, type checking, production build, JSON validation, and diff whitespace checks.
- **Status:** complete

### Phase 16: Team Membership Invites & Folder Permission Boundary
- [x] Add backend TDD coverage for team creation, invites, member role updates/removal, audit events, and team-folder read/write permissions.
- [x] Expose `/teams`, `/teams/{team_id}`, `/teams/{team_id}/invites`, and member join/update/remove routes in the FastAPI/OpenAPI contract.
- [x] Regenerate the OpenAPI client so frontend code uses generated team SDK calls through `src/client/workspace.ts`.
- [x] Add Pinia workspace team detail, invite, role update, removal, and loading state while keeping auth/session ownership in `auth/`.
- [x] Replace the read-only team panel with a Naive UI + UnoCSS team creation, team detail, invite, member-role, and audit surface.
- [x] Re-run backend tests, frontend focused/all tests, type checking, production build, JSON validation, and diff whitespace checks.
- **Status:** complete

### Phase 17: Knowledge Base CRUD & Interactive RAG Panel
- [x] Add backend TDD coverage for knowledge-base create/update, document indexing, audited QA citations, and OpenAPI paths.
- [x] Expose `/knowledge-bases`, `/knowledge-bases/{kb_id}`, and `/knowledge-bases/{kb_id}/documents` in the FastAPI/OpenAPI contract.
- [x] Regenerate the OpenAPI client so frontend code uses generated knowledge-base SDK calls through `src/client/workspace.ts`.
- [x] Add Pinia workspace knowledge-base state/actions for list, create, document load/add, active selection, and question asking while keeping auth/session ownership in `auth/`.
- [x] Replace the read-only RAG panel with a Naive UI + UnoCSS knowledge-base creation, document indexing, question, answer, and citation surface.
- [x] Wire `WorkspaceView.vue` to pass store refs and events into `RagInsightPanel.vue`.
- [x] Re-run backend tests, frontend focused/all tests, type checking, OpenAPI generation, production build, JSON validation, and diff whitespace checks.
- **Status:** complete

### Phase 18: Editable Workflow Definitions & Builder UI
- [x] Add backend TDD coverage for workflow create/update/validate/publish/execute and OpenAPI paths.
- [x] Expose workflow definition mutation routes while preserving deterministic in-memory execution and audit events.
- [x] Regenerate the OpenAPI client so frontend code uses generated workflow SDK calls through `src/client/workspace.ts`.
- [x] Add Pinia workspace workflow state/actions for active workflow, validation, publication, execution, and timeline updates while keeping auth/session ownership in `auth/`.
- [x] Replace the read-only workflow list with a Naive UI + UnoCSS workflow builder panel using Vue Flow for node/edge preview.
- [x] Wire `WorkspaceView.vue` to pass files, knowledge bases, workflow refs, and workflow events into `AgentWorkflowPanel.vue`.
- [x] Re-run backend tests, frontend focused/all tests, type checking, production build, JSON validation, and diff whitespace checks.
- **Status:** complete

### Phase 19: Cross-Resource RBAC Enforcement
- [x] Add backend TDD coverage for team-file visibility, member/guest read-write behavior, knowledge-base document indexing denial, and workflow execution denial.
- [x] Route file listing through the authenticated user so team files are filtered by folder/team membership.
- [x] Add shared file read/write checks and apply them to download, versions, update, copy, restore, delete, knowledge-base indexing, RAG citation filtering, agent context files, and workflow execution.
- [x] Adjust workflow execution coverage so team-file execution uses an explicit team owner context instead of unauthenticated seed-team access.
- [x] Regenerate the OpenAPI client after the backend phase and re-run backend/frontend verification, JSON validation, services-boundary check, and diff whitespace check.
- **Status:** complete

### Phase 20: Resource ACL Rules & Permission Panel
- [x] Add backend TDD coverage for permission rule list/create/delete, explicit deny precedence, inherited folder rules, file-level override rules, and audit events.
- [x] Expose `/permissions/rules` routes in the FastAPI/OpenAPI contract with typed subject/resource/action/effect schemas.
- [x] Store deterministic in-memory ACL rules and apply them through the shared folder/file read/write permission helpers from Phase 19.
- [x] Regenerate the OpenAPI client so frontend code uses generated permission SDK calls through `src/client/workspace.ts`.
- [x] Add Pinia permission-rule state/actions and a Naive UI + UnoCSS file permission panel without reintroducing `services/`.
- [x] Re-run backend tests, frontend focused/all tests, type checking, production build, JSON validation, services-boundary check, and diff whitespace check.
- **Status:** complete

### Phase 21: Remote Merge — Full-Page Views & Guest Auth
- [x] Merge remote `frontend` branch: 4 new standalone views added.
- [x] `WorkflowBuilderView.vue` — drag/drop Vue Flow orchestration with node presets, execution history, and full-page workspace layout.
- [x] `TeamChatView.vue` — team collaboration chat with @mentions, file attachments, team notices, and member sidebar.
- [x] `RagQaView.vue` — standalone RAG Q&A page with question input, citations, and source file display.
- [x] `PermissionAuditView.vue` — admin-only audit log with role-based filtering and permission rule listing.
- [x] Guest login support: `selectedAccessRole` in auth store, readonly/guest role switching.
- [x] Router guards: `requiresAdmin` meta for `/permission-audit`, `canAccessPermissionAudit` check.
- [x] Backend: demo user seeding (`_seed_demo_user`), permission backend routes merged.
- [x] Resolve merge conflicts across 6 files (routes, services, tests, AgentWorkflowPanel, RagInsightPanel, vite.config).
- [x] Update findings, task_plan, and progress documentation.
- **Status:** complete

### Phase 22: File Search Updated-Time Range
- [x] Add backend TDD coverage for FR-F07 updated-time filtering on `GET /api/v1/files`.
- [x] Add inclusive `updated_from`/`updated_to` query params and service filtering.
- [x] Regenerate the OpenAPI client and map `updatedFrom`/`updatedTo` through the workspace adapter/store.
- [x] Add visible FileWorkbench time-range controls and focused frontend tests.
- [x] Re-run backend tests, frontend tests, type checking, build, JSON validation, and diff whitespace checks.
- **Status:** complete

### Phase 23: File Annotations & Replies
- [x] Add backend TDD coverage for annotation list/create/reply/delete, permissions, audit events, and notification signals.
- [x] Expose `/files/{file_id}/annotations`, `/annotations/{annotation_id}/replies`, and delete routes in the FastAPI/OpenAPI contract.
- [x] Regenerate the OpenAPI client and add generated-client-backed annotation adapters/store actions.
- [x] Add `FileAnnotationPanel.vue` and wire it through `FileWorkbench.vue` and `WorkspaceView.vue`.
- [x] Re-run backend tests, frontend tests, type checking, build, JSON validation, and diff whitespace checks.
- **Status:** complete

### Phase 24: Notification Inbox API/UI
- [x] Add backend TDD coverage for listing and marking notifications read across invites, mentions, annotation replies, and workflow completion.
- [x] Add `/notifications` list and `/notifications/{notification_id}/read` routes with typed schemas and OpenAPI assertions.
- [x] Replace derived unread counts with per-user in-memory notification entities and audit `notification.read`.
- [x] Regenerate the OpenAPI client and add notification adapters/store state/actions.
- [x] Add `NotificationInboxPanel.vue` and compose it inside `TeamAuditPanel.vue` via `WorkspaceView.vue`.
- [x] Re-run focused and full backend/frontend verification, type checking, build, JSON validation, and diff whitespace checks.
- **Status:** complete

### Phase 25: Document Parser Integration & Verification
- [x] Remove dead `_chunk_file_content()` method replaced by real parser.
- [x] Add `backend/tests/test_parser.py` with 21 unit tests covering all 6 formats (PDF/DOCX/PPTX/TXT/MD/CSV), error handling, and segment metadata.
- [x] Add parser integration tests to `test_workspace_api.py` for KB indexing lifecycle, parse failure handling, and QA citation flow.
- [x] Regenerate the OpenAPI client and verify frontend parse_status display.
- [x] Re-run full backend/frontend verification, type checking, build, JSON validation, and diff whitespace checks.
- **Status:** complete

### Phase 26: Semantic Embedding & FAISS Vector Search
- [x] Create `backend/app/services/embedding.py` wrapping sentence-transformers (MiniLM-L12-v2, 384-dim) with lazy loading and zero-vector fallback.
- [x] Integrate FAISS `IndexFlatIP` per knowledge base: rebuild index after document add, search with inner product (cosine).
- [x] Replace character-overlap `_chunk_score()`/`_search_chars()` with FAISS semantic search in `_retrieve_knowledge_citations()`.
- [x] Fix `_compose_rag_answer()` — remove hardcoded microscope response, use generic snippet composition.
- [x] Add `backend/tests/test_embedding.py` with 10 tests covering shape, normalization, semantic similarity, cross-language, and FAISS retrieval integration.
- [x] Re-run full verification: 66 backend tests, 62 frontend tests, type check, build all pass.
- **Status:** complete

### Phase 27: LLM Answer Generation Service
- [x] Create `backend/app/services/llm.py` wrapping langchain-openai ChatOpenAI with graceful template fallback when unconfigured.
- [x] Integrate LLM into `_compose_rag_answer()` — uses real LLM when `OPENAI_API_KEY` is set, otherwise concatenates snippets.
- [x] Chinese prompt template with source citation requirements.
- [x] Add `backend/tests/test_llm.py` with 5 tests covering availability check, template fallback, empty snippets, and API key configuration.
- [x] Full verification: 71 backend tests pass.
- **Status:** complete

### Phase 28: RAG And Agent Flow Refactor
- [x] Add scoped v2 knowledge-base metadata: personal/team scope, category, tags, freshness policy, archive/delete status, and last indexed timestamp.
- [x] Add knowledge-base batch file membership: list files, batch add, batch remove, reindex, partial success reporting, and OpenAPI export coverage.
- [x] Persist v2 RAG conversations: conversation summaries, message history, assistant `message_id`, citation snapshots, and deterministic prior-question context handling.
- [x] Add deterministic tool registry and agent executor: `calculator`, `course_lookup`, `file_content_search`, `python_data`, explicit understand/plan/call/observe/answer phases, `needs_clarification`, result views, task detail, and continue routes.
- [x] Regenerate the frontend OpenAPI client and add typed adapters for KB batch/reindex/conversation endpoints, tools, and agent detail/continue.
- [x] Split RAG frontend state into `stores/knowledge.ts` and compose `/rag` from `KnowledgeBaseSidebar`, `KnowledgeBaseManager`, `KnowledgeFilePicker`, `KnowledgeConversationPanel`, and `KnowledgeCitationList`.
- [x] Split agent frontend state into `stores/agent.ts` and compose `/workflow` agent execution panels from `AgentTaskComposer`, `ToolCatalogPanel`, `AgentExecutionTimeline`, and `ToolResultViewer`.
- [x] Extract RAG retrieval/answer generation into `backend/app/services/rag_pipeline.py` while keeping existing service methods stable.
- [x] Add explicit RAG no-result/index-state error codes: `KB_EMPTY`, `KB_FILE_NOT_INDEXED`, and `KB_NO_MATCH`.
- [x] Full verification: backend `92 passed, 3 warnings`; frontend `67` unit tests passed; frontend type-check and production build passed; JSON and diff hygiene passed.
- **Status:** complete; transitional workspace-store compatibility remains intentionally because legacy workspace panels still consume it.

### Phase 29: Personal Folder Baseline Hardening
- [x] Add backend coverage proving initial users get per-user personal root folders.
- [x] Normalize missing or legacy file upload folder ids to `personal-root-{user.id}`.
- [x] Complete multipart upload using real chunks and the normal upload path.
- [x] Cover personal folder create, rename, move, delete, root protection, and file rehome behavior.
- [x] Verify frontend file manager create/rename/delete/upload flows do not depend on a global `personal-root`.
- **Status:** complete

### Phase 30: Complete Tool-Flow Backend
- [x] Persist agent tasks/steps instead of process-memory dictionaries.
- [x] Replace single-tool routing with ordered multi-step planning and execution.
- [x] Move tool data sources out of inline mock/hardcoded runtime data.
- [x] Add clarification resume, retry/fallback, and structured result-view contracts.
- [x] Remove or isolate legacy placeholder agent helper paths.
- **Status:** complete

### Phase 31: Tool-Flow Web UI And System Evaluation
- [x] Extend workflow result UI for multi-step traces and text/table/chart/mixed results.
- [x] Add frontend tests for multi-tool mixed and chart result states.
- [x] Add 10+ backend system test cases with completion-rate and tool-selection-accuracy metrics.
- [x] Document typical successful and failed cases under `docs/superpowers/reports/`.
- [x] Run backend/frontend full verification, build, JSON validation, and diff hygiene.
- **Status:** mostly complete; persisted task-history listing endpoint remains a follow-up if required by the UI.

### Phase 32: LLM Tool-Calling Contract
- [x] Define strict JSON schema for LLM planner output.
- [x] Implement `ToolCallingLLM` around existing OpenAI-compatible config.
- [x] Add deterministic fallback planner for CI/no-key local runs.
- [x] Add tests for plan parsing, invalid JSON repair, missing-field clarification, and no-key fallback.
- **Status:** complete

### Phase 33: Iterative Agent Loop
- [x] Refactor `AgentExecutor` into a bounded plan-call-observe-revise loop.
- [x] Add max tool calls, retry limits, and timeout behavior.
- [x] Persist plan revisions, tool calls, observations, and final answer through existing agent step persistence.
- [x] Add cancel behavior and API route.
- **Status:** complete

### Phase 34: Real Tool Expansion
- [x] Add `rag_query`, `database_query`, `weather_lookup`, and `file_metadata_query` as configured/permissioned tools.
- [x] Keep existing calculator, file content search, CSV analysis, and course lookup.
- [x] Add schema, permission, and result-view mapping for every tool.
- **Status:** complete

### Phase 35: Agent Memory And Multi-Turn Conversation
- [x] Store user/assistant messages per task.
- [x] Continue tasks with follow-up questions and prior observations.
- [x] Summarize long histories before sending to LLM.
- [x] Return persisted task detail with messages, tool-call snapshots, and plan revisions from create/continue APIs.
- **Status:** complete; task detail now includes messages, tool-call snapshots, and plan revisions.

### Phase 36: Web UI Upgrade
- [x] Add task history list, active task detail, continue/cancel controls.
- [x] Show LLM-generated plan, tool arguments, retries, latency, and output summaries.
- [x] Add plan preview and confirmation before executing medium/high risk tool plans.
- [x] Add streaming plan/tool/final-answer event UI through the agent SSE event-stream contract.
- **Status:** complete

### Phase 37: Security And Operations
- [x] Enforce access checks before every tool call.
- [x] Add role/tool allowlists, audit logs, config validation, and structured metrics.
- **Status:** complete

### Phase 38: Evaluation And Acceptance
- [x] Expand system evaluation to at least 25 cases.
- [x] Track completion rate, tool selection accuracy, argument accuracy, citation rate, and latency.
- [x] Document success/failure examples and known limitations.
- **Status:** complete

### Phase 39: RAG Backend Document-Level Context Refactor
- [x] Add regression tests for broad document-explanation prompts such as “讲解这些文档”, “总结知识库所有文件”, and “分别说明每个文档讲了什么”.
- [x] Extend knowledge document storage with cleaned full text, outline/section metadata, document summary, keywords, token/character counts, and indexing diagnostics.
- [x] Replace query-only top-k chunk prompting with an intent-aware context planner that supports targeted QA, single-document explanation, multi-document overview, comparison, and report modes.
- [x] Add a document-level retriever path that can enumerate readable indexed documents and assemble map-reduce summaries before final answer generation.
- [x] Move full-document fallback out of `WorkspaceServiceDB.answer_question()` into `RagPipeline`, and make stream/non-stream use the same context-building code.
- [x] Redesign LLM prompt inputs from `list[str] snippets` into structured context blocks with document cards, selected sections, citations, and explicit answer policy.
- [x] Add no-result behavior that distinguishes empty KB, unindexed files, weak retrieval for broad prompts, and real no-match cases.
- [x] Reindex existing documents through the new pipeline and add OpenAPI-compatible diagnostics without breaking the current `QAResponse` citation contract.
- [x] Run backend focused RAG tests, full backend tests, OpenAPI export, and frontend client generation if schemas change.
- **Status:** complete; existing already-indexed rows without `content_text` still fall back to stored chunks until reindexed.

## Key Questions
1. Which report requirements define the initial MVP? Answer: section 7.1 of `report/requirements/requirements_specification.md`.
2. Which architecture must the implementation follow? Answer: Vue 3 + Vite + TypeScript frontend and FastAPI backend under `/api/v1`, with module boundaries from `report/design/system_design_specification.md`.
3. How far should this turn go? Answer: make concrete progress toward a working vertical slice while preserving the full platform scope.

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Build a deterministic in-memory MVP before wiring MySQL/MinIO/FAISS | The repo currently contains only starter scaffolds; the report requires many modules, so a tested API/UI skeleton creates the right boundaries without pretending the full infrastructure exists. |
| Keep backend modules aligned to report domains | Requirements NFR-M01 explicitly asks for user/auth, file, knowledge, agent, workflow, team, permission/audit separation. |
| Use Chinese UI copy and dense workbench layout | Root `DESIGN.md` and design section 9 require an operational academic workspace, not a landing page. |
| Add appropriate dependencies when they improve correctness or workflow | The user explicitly allowed adding suitable dependencies; avoid contorting implementation just to minimize dependency count. |
| Keep auth separate from generated client output | `auth/` owns session persistence and header helpers; `client/generated/` remains replaceable output from OpenAPI generation. |
| Enforce access/refresh token kinds in the in-memory auth boundary | Refresh tokens can rotate sessions but cannot access protected resources; access tokens cannot refresh sessions. This preserves the intended contract before persistent token storage is added. |
| Implement profile maintenance as an auth-domain slice | `PATCH /users/me` belongs to the report's user/auth API contract; frontend state remains in `stores/auth.ts`, and the page lives in `views/ProfileView.vue` rather than `layouts/`. |
| Keep generated client same-origin and proxy only in Vite dev | The OpenAPI-generated fetch client keeps `baseUrl: '/'`; during local development Vite proxies `/api` to FastAPI at `http://127.0.0.1:8000`, avoiding hard-coded backend URLs in app code. |
| Implement FR-U05 before persistence | The report requires failed-login lockout. The MVP stores failed attempts in the in-memory auth service now, while keeping the API/OpenAPI/error contract stable for a later database-backed security state. |
| Add file download/delete before storage persistence | The report requires file download and delete. The MVP now stores bytes in memory and exposes stable API/generated-client/frontend contracts, leaving MinIO/object-storage replacement as a later repository-layer change. |
| Wire existing file search/upload backend contracts into the frontend before adding folder CRUD | `/api/v1/files` query parameters and `/api/v1/files/upload` already exist in the generated SDK, so Phase 13 improves the daily file workflow without expanding backend scope. |
| Implement folder CRUD as a tree contract before storage persistence | FR-F02 needs nested create/move/delete, tree navigation, and breadcrumbs. The MVP keeps folders in memory but stabilizes backend/OpenAPI/generated-client/store/UI boundaries for later database storage. |
| Implement file lifecycle operations before persistence | FR-F01 and FR-F05 require rename/move/copy/tags plus version listing and rollback. The MVP keeps file bytes and versions in memory while stabilizing API/OpenAPI/generated-client/store/UI contracts for later object storage and database repositories. |
| Implement team membership and folder permissions as one boundary | Team invites, member roles, and team-root folder read/write checks are coupled in FR-C01/C02/C03/C08/C10, so Phase 16 stabilizes them together across backend, OpenAPI, generated client, Pinia, and the team panel UI. |
| Implement knowledge-base CRUD and RAG citations before real vector storage | The report requires knowledge-base creation, document indexing, and cited QA. The MVP keeps deterministic chunks in memory while stabilizing backend/OpenAPI/generated-client/store/UI contracts for later FAISS/Milvus and LLM replacement. |
| Implement editable workflow definitions before advanced visual editing | FR-W01/W04/W05/W06 require create/update/validate/publish/execute contracts. The MVP now stores DAG definitions in memory, previews them with Vue Flow, and keeps drag/drop node editing as a later workflow-editor refinement. |
| Enforce team-file RBAC at shared file read/write boundaries before adding ACL configuration UI | FR-C08/C09/NFR-S04 require resource access to pass RBAC before file, knowledge, agent, and workflow operations. Phase 19 applies role-aware checks across existing runtime paths without expanding the OpenAPI surface into a full permission-matrix editor yet. |
| Add ACL rules before persistent permission repositories | FR-C08/C09/C10 require resource-level allow/deny, inheritance, overrides, and audit events. Phase 20 keeps the rules in memory and wires them into existing shared file/folder permission helpers so later MySQL repositories can replace storage without changing API/UI contracts. |
| Add notification inbox entities before WebSocket delivery | FR-C07 requires durable notification records and read state. Phase 24 keeps notification storage in memory for now, exposes stable API/OpenAPI/generated-client/store/UI contracts, and leaves live push delivery as a later WebSocket slice. |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| `uv pip install` waited on `.venv/.lock` | 1 | Ran backend test commands from `backend/` with `uv run --no-project --with ...` while the existing `uv sync` owns the lock. |
| Frontend build failed on stale Vue starter files | 1 | Removed unused starter tests/views after the workspace replaced the default screen. |
| UnoCSS line-height classes compressed text | 1 | Replaced `leading-1.65`-style classes with `leading-[1.65]` arbitrary values. |
| Mobile workbench had horizontal overflow | 1 | Added Naive DataTable `scroll-x` and constrained cards with `min-w-0 overflow-hidden`. |
| Generated hey-api client used `baseUrl: 'src'` | 1 | Added FastAPI `servers=[{"url": "/"}]`, regenerated OpenAPI, and verified generated `baseUrl: '/'`. |
| Login view used unavailable `NSegmented` | 1 | Replaced it with Naive UI `NRadioGroup` and `NRadioButton` in solid button style. |
| Refresh endpoint initially returned 404 during TDD | 1 | Added `RefreshTokenRequest`, `/auth/refresh`, service refresh logic, and regenerated the client. |
| Frontend auth store initially lacked `refreshSession()` | 1 | Added the generated-client-backed action and persisted rotated access/refresh tokens. |
| Profile update endpoint initially returned 405 during TDD | 1 | Added `UserUpdate`, `PATCH /users/me`, service update logic, and regenerated the client. |
| Frontend profile route/store/view were initially missing | 1 | Added `updateProfile()`, protected `/profile`, `ProfileView.vue`, and focused tests. |
| Frontend architecture test rejected the existing Vite proxy string/target | 1 | Updated `frontend/vite.config.ts` to proxy `'/api'` to `http://127.0.0.1:8000`. |
| Login lockout backend tests initially lacked `failed_attempts` details | 1 | Added per-user login security state, structured details, lockout response, success reset, and audit events. |
| Login OpenAPI responses initially lacked 401/423 schemas | 1 | Added login `responses` metadata using `ErrorResponse` and regenerated the frontend client. |
| Frontend auth store initially displayed lockout as a generic password error | 1 | Added generated-error narrowing and `ACCOUNT_LOCKED` message mapping. |
| File download/delete backend tests initially returned 404 | 1 | Added file content storage, download/delete service methods, routes, and audit events. |
| Frontend file-action tests initially lacked generated-client adapters and row controls | 1 | Added `downloadWorkspaceFile`, `deleteWorkspaceFile`, workspace store actions, and FileWorkbench download/delete emits. |
| Production build failed because `resolveAccessToken()` returned `string | undefined` | 1 | Split optional and required token helpers so TypeScript sees required file actions as receiving a `string` token. |
| File search/upload component failed to compile because a `defineProps` default referenced `emptyFilters` | 1 | Inlined the default filters object in the `withDefaults()` macro because Vue hoists `defineProps`. |
| Type check rejected `demoWorkspaceSnapshot.files[0]` in tests | 1 | Added a fixture helper that explicitly finds the demo file and throws if it is absent, preserving `FileItem` typing. |
| Backend folder CRUD tests initially returned 404 and OpenAPI lacked folder paths | 1 | Added folder schemas, routes, in-memory tree mutation service methods, validation errors, audit events, and OpenAPI assertions. |
| Frontend folder tests initially lacked adapters/store actions/component | 1 | Added generated-client-backed folder adapters, Pinia folder tree actions, `FolderTreePanel.vue`, dynamic upload folder options, and view wiring. |
| Frontend team store test hit missing team-summary merge helpers | 1 | Added immutable `upsertTeamSummary()`, `mergeTeamMember()`, and `teamDetailToSummary()` helpers for the `shallowRef` workspace snapshot/team detail state. |
| TeamAuditPanel tests could not find team creation, invite, and member controls | 1 | Replaced the read-only team list with typed props/emits, Naive UI forms/buttons, role labels, and member management controls. |
| WorkspaceView RAG wiring test could not find knowledge-base controls | 1 | Passed knowledge-base refs into `RagInsightPanel.vue` and wired create/select/add-document/ask events to workspace store actions. |
| Workspace store KB test expected the pre-index create response after adding a document | 1 | Updated the test assertion to expect post-index document count, chunk count, and document timestamp. |
| Workflow builder tests initially found only the old read-only workflow panel | 1 | Replaced `AgentWorkflowPanel.vue` with typed create/select/save/validate/publish/execute emits, Vue Flow preview, and view/store wiring. |
| Workflow panel type check rejected generated position maps and test emitted payload typing | 1 | Normalized Vue Flow node positions to explicit `x`/`y` coordinates and added typed test guards for emitted payloads. |
| Full backend tests initially failed after RBAC enforcement because a workflow test executed the seeded team file without team membership | 1 | Updated the workflow test to create a team as the current user, upload a team file into that folder, then execute the workflow with an explicit owner context. |
| Permission-rule backend tests initially lacked ACL routes and evaluation | 1 | Added permission rule schemas/routes, in-memory ACL storage, deny precedence, folder inheritance, file overrides, and audit events. |
| Frontend permission-rule tests initially lacked adapters/store actions/panel wiring | 1 | Added generated-client-backed permission adapters, Pinia permission rule state/actions, `PermissionRulesPanel.vue`, and FileWorkbench/WorkspaceView props/events. |
| `PermissionRulesPanel.vue` type check rejected first-option array indexing | 1 | Assigned the first select option to a local constant and guarded it before reading `.value`, satisfying strict TypeScript. |
| Notification API tests initially returned 404 | 1 | Added notification schemas, service storage, list/read routes, unread-count derivation, and OpenAPI assertions. |
| Frontend notification tests initially lacked adapters/store actions/panel wiring | 1 | Added generated-client-backed notification adapters, Pinia inbox state/actions, `NotificationInboxPanel.vue`, and TeamAuditPanel/WorkspaceView props/events. |

## Notes
- This is a working report-aligned MVP vertical slice, not the full production platform.
- Remaining production gaps: server-side JWT persistence/rotation invalidation, database/object storage, persistent permission repositories/admin policy matrix, real parser/vector index, live LLM tool execution, drag/drop workflow node editing, and WebSocket collaboration.
