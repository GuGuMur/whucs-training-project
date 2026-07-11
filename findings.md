# Findings & Decisions

## Requirements
- Read the relevant documents under `report/` and develop a frontend-backend separated intelligent file management and agent collaboration platform.
- Required architecture from `report/design/system_design_specification.md`: Vue 3 + Vite + TypeScript frontend; FastAPI backend; REST and WebSocket-ready API layer; domain services for auth, files, RAG, agents, workflows, teams, permissions, and audit.
- MVP scope from `report/requirements/requirements_specification.md` section 7.1:
  - User registration, login, and JWT authentication.
  - Personal file/folder CRUD.
  - File upload, download, delete, search, and tag filtering.
  - Basic parsing for PDF/DOCX/PPTX/TXT/MD/CSV.
  - Knowledge base creation, chunking, vector indexing, and natural-language Q&A.
  - Basic teams, invites, team folders, and roles.
  - At least three agent tools: file search, knowledge Q&A, report generation.
  - At least one runnable workflow template: new-file automatic summary.
- API base path must be `/api/v1`; errors should use a structured `code`, `message`, `detail` shape.
- UI must be an operational workbench with sidebar, top bar, central file/knowledge/workflow area, and context panels; no marketing landing page.

## Research Findings
- Current frontend is the default Vue starter app with Vue Router, Pinia, Naive UI, Vue Flow, axios, and testing/build scripts already installed.
- Current backend has dependencies for FastAPI, SQLAlchemy, JWT, LangChain, FAISS/Milvus, document parsing, Redis/Celery/ARQ, but the tracked `backend/main.py` placeholder is currently deleted in the worktree.
- Root `DESIGN.md` defines the visual contract: calm academic operations workspace, Chinese UI copy, restrained blue primary, semantic status chips, dense tables/lists, and visible parsing/RAG/workflow/permission states.
- Project-specific prototype skill confirms sample domain data: teams `生物学实验`, `软件工程课程组`; files `显微镜实验报告.pdf`, `需求规格说明书.md`, `小组周报.docx`; tools `file_search`, `knowledge_qa`, `image_ocr`, `file_compare`, `report_generate`.
- 2026-07-11 RAG backend audit: v2 Q&A routes use `WorkspaceServiceDB` and `RagPipeline`, while the older in-memory `WorkspaceService` still keeps a separate retrieval/answer implementation. The live DB-backed path stores `KnowledgeDocument` and `KnowledgeChunk` only; it does not persist cleaned full text, document outline, summary, keywords, section hierarchy, or document-level statistics.
- 2026-07-11 RAG backend audit: `WorkspaceServiceDB.add_knowledge_document()` parses a file, cleans text, chunk-splits it at about 600 characters, prefixes chunks with `[filename]`, and stores only chunks. Parse failures are swallowed into a one-chunk filename-only “indexed” document, which can create misleading answers instead of actionable parse errors.
- 2026-07-11 RAG backend audit: `WorkspaceServiceDB.answer_question()` performs vector retrieval first and only injects a full document when at least half of the retrieved citations come from one document. Broad prompts like “讲解这些文档” have weak retrieval signals and can miss the actual documents, so the answer generator may conclude that references are insufficient.
- 2026-07-11 RAG backend audit: stream and non-stream answer paths duplicate context-building logic, and `report_mode` is not passed through in `_stream_llm()`. This increases drift risk when fixing RAG behavior.
- 2026-07-11 RAG backend audit: `generate_rag_answer()` accepts unstructured `list[str]` snippets. This prevents the prompt from reliably knowing which document each block belongs to, whether context is full-document/summary/section/chunk, and how to answer document-level overview tasks.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Start with a tested in-memory FastAPI MVP | It can satisfy route contracts and frontend integration while keeping database/object-store/vector-store wiring replaceable. |
| Implement frontend as a workbench shell first | It creates the user-facing module map required by the report and gives the backend endpoints a concrete consumer. |
| Treat LLM/RAG behavior as deterministic demo services initially | Network API keys and vector infrastructure are not configured; deterministic behavior is testable and can expose citations, agent steps, and workflow status now. |
| Add suitable dependencies when needed | The user explicitly confirmed dependencies can be added when appropriate, so implementation should prefer correctness and maintainability over avoiding dependency declarations. |
| Add refresh-token rotation contract before persistence | The in-memory service now distinguishes access and refresh token kinds, rotates both tokens on refresh, and keeps persistence/blacklist hardening as a later repository-layer concern. |
| Keep profile maintenance in the auth domain | FR-U04 maps to `PATCH /users/me`; backend owns email uniqueness and audit logging, frontend auth store owns generated-client update state, and `ProfileView.vue` stays in `views/`. |
| Implement login lockout as an auth-domain security slice | FR-U05 now has a stable backend/runtime/OpenAPI/frontend contract: 5 consecutive failures lock the user for 5 minutes, return `ACCOUNT_LOCKED`, and write audit events. Database-backed persistence remains a later repository-layer concern. |
| Implement file download/delete as a file-domain lifecycle slice | The report requires download/delete. The backend now exposes stable REST/OpenAPI contracts, the frontend calls generated SDK functions through `src/client/workspace.ts`, and `FileWorkbench.vue` emits row actions without owning API state. |
| Implement file move/copy/versioning after folder CRUD | Rename/move/copy and version rollback need valid folder targets, so FR-F01/FR-F05 now sit on top of the folder tree contract. Backend owns validation/version semantics; frontend uses generated SDK adapters, Pinia loading state, and a focused `FileLifecyclePanel.vue`. |
| Implement team membership and team-folder permission checks together | Invites, member role changes, removal, audit events, and team folder write boundaries are one collaboration contract. Backend owns role/read-write enforcement; frontend uses generated SDK adapters, Pinia team state, and a focused `TeamAuditPanel.vue`. |
| Implement knowledge-base CRUD and cited QA before external vector infrastructure | The report requires creating knowledge bases, indexing documents, and asking questions with citations. The current contract keeps chunking/retrieval deterministic and in memory, while backend/OpenAPI/generated-client/Pinia/UI boundaries are ready for FAISS/Milvus and LLM replacement. |
| Implement editable workflow definitions before advanced visual editing | The report workflow requirements need stable create/update/validate/publish/execute contracts before drag/drop editing. Backend now owns DAG validation and deterministic execution; frontend uses generated SDK adapters, Pinia workflow state, and a Vue Flow preview panel. |
| Enforce RBAC through shared file read/write checks before ACL editor work | FR-C08/C09 and NFR-S04 require resource checks before file, knowledge, agent, and workflow operations. Phase 19 now filters team files in listing and rejects unauthorized read/write paths while keeping configurable ACL inheritance/overrides for a later UI/API phase. |
| Implement in-memory ACL rules before database permission repositories | FR-C08/C09/C10 call for resource-level allow/deny, inheritance, overrides, and audit logs. Phase 20 keeps rules in memory and wires them through shared file/folder permission helpers, preserving API/frontend contracts for a later MySQL-backed `permission_rules` table. |
| Add full-page views for workflow builder, team chat, RAG Q&A, and permission audit | The remote `frontend` branch contributed 4 standalone views: `WorkflowBuilderView.vue` (drag/drop Vue Flow node editing with execution history), `TeamChatView.vue` (team chat with @mentions, attachments, and notices), `RagQaView.vue` (standalone Q&A page with citations and source files), and `PermissionAuditView.vue` (admin-only audit log with role-based filtering). |
| Support guest login and role-based routing | The remote branch added `selectedAccessRole` to the auth store with guest/readonly support, `requiresAdmin` router meta for `/permission-audit`, and `canAccessPermissionAudit` guard. |
| Seed demo user for immediate login | Remote `permission-backend` added `_seed_demo_user()` with xiaoming/xiaoming@example.com/Str0ngPass! so new installations have a working login out of the box. |
| Implement resumable multipart upload as the next file-management slice | FR-F03/NFR-R03 require large-file chunking and resume-ready state. Backend now owns init/chunk/status/complete contracts with chunk SHA256 validation and final file SHA256 validation; frontend has generated-client wrappers plus a Pinia `uploadLargeFile()` action while regular upload behavior remains unchanged. |
| Implement share links as short-lived signed download tokens | FR-F08/NFR-S05 require configurable share links and download links no longer than 1 hour. Backend now creates read-authorized share tokens with optional password, expiry, download limit, audit events, and a public download endpoint; frontend has generated-client wrappers plus a Pinia `createFileShareLink()` action. |
| Implement soft delete with a recycle-bin restore contract | FR-F09 and the design spec describe `DELETE /files/{file_id}` as soft delete. Backend now keeps file bytes/versions while moving active metadata into an in-memory recycle bin, exposes `GET /files/recycle-bin` and `POST /files/{file_id}/restore`, and frontend reaches those routes only through generated-client adapters and Pinia actions. |
| Complete FR-F07 time-range file filtering on the existing file-list contract | File search already supported filename query, tag, and file type filters. The remaining updated-time range now uses `updated_from`/`updated_to` query parameters on `GET /api/v1/files`, maps to `updatedFrom`/`updatedTo` in the frontend adapter/store, and is emitted from the existing FileWorkbench toolbar. |
| Add file annotations and replies as a collaboration slice | US-T03/FR-C05/FR-C07 now has backend annotation list/create/reply/delete contracts, audit events, and team unread-count notification signals. Frontend uses generated-client adapters, Pinia annotation state keyed by file id, and a focused `FileAnnotationPanel.vue` composed by `FileWorkbench.vue`. |
| Add notification inbox records before WebSocket push | FR-C07 now has per-user notification list/read contracts for team invites, mentions, annotation replies, and workflow completion. The MVP keeps records in memory and wires generated-client/Pinia/UI read state, while live WebSocket delivery remains a later production slice. |
| Integrate real multi-format document parser before async queue | FR-K02 requires PDF/DOCX/PPTX/TXT/MD/CSV parsing. Backend now owns `parser.py` with lazy-loaded extractors (PyMuPDF, python-docx, python-pptx, csv). `add_knowledge_document()` runs the real parser with parse_status lifecycle `queued → parsing → indexed/failed`. Dead `_chunk_file_content()` removed. 21 parser unit tests + 3 integration tests added. Async ARQ/Celery queue deferred per NFR-P05. |
| Replace keyword search with semantic FAISS vector search | FR-K04/K05 require embedding and vector indexing. Backend now owns `embedding.py` (sentence-transformers MiniLM-L12-v2, 384-dim, lazy-loaded with zero-vector fallback for CI). Per-KB `faiss.IndexFlatIP` replaces character-overlap `_chunk_score()`/`_search_chars()`. Hardcoded microscope answer removed. 10 embedding tests + FAISS retrieval integration test added. Total: 66 backend tests. |
| Fix RAG with document-level context planning instead of larger chunk stuffing | The failure mode is not just low `top_k`; broad prompts require enumerating and summarizing documents, while targeted QA should keep chunk retrieval. The backend should classify query intent, build structured context blocks, and use map-reduce document summaries when the request is about “these documents” or the whole KB. |
| Keep agent fallback rules authoritative over unsafe LLM tool plans | During Phase 39 verification, the LLM planner over-selected tools with empty required parameters. The planner now falls back to deterministic direct-answer behavior when rules say no tool is needed, skips optional empty-argument tools, and uses fallback-extracted arguments for retained tools. |
| Persist agent memory from the API response boundary | Phase 35 should not only store raw task rows; create/continue responses must reload persisted messages, tool-call snapshots, and plan revisions so API clients see the durable task state immediately. Long histories are compacted into a system summary plus recent turns before the next run. |
| Keep Phase 36 streaming UI behind a real event-stream contract | The frontend now exposes persisted history, details, continuation, cancellation, plan/tool metadata, retries, latency, and summaries. It should not fake streaming plan/tool/final-answer events until the backend has an SSE or WebSocket contract. |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| Refresh endpoint and frontend refresh action were missing during TDD | Added backend `/api/v1/auth/refresh`, regenerated the OpenAPI client, and added `refreshSession()` in the auth store. |
| Profile endpoint and frontend page were missing during TDD | Added backend `/api/v1/users/me` PATCH, regenerated the OpenAPI client, and added protected `/profile` with a Naive UI profile form. |
| Login lockout behavior was missing during TDD | Added backend failed-attempt state, OpenAPI 401/423 error schemas, generated client types, and frontend lockout message mapping. |
| File download/delete behavior was missing during TDD | Added backend in-memory file bytes, download/delete routes, regenerated the OpenAPI client, and wired frontend store/component row actions. |
| Workspace store file-action token helper was too loose for TypeScript | Split optional token resolution for workspace loading from required token resolution for file actions. |
| File lifecycle update/copy/version UI was missing during TDD | Added backend lifecycle/version contracts, regenerated the client, then wired workspace adapters, Pinia actions, `FileLifecyclePanel.vue`, and `WorkspaceView` handlers. |
| Team membership and folder permission behavior was missing during TDD | Added backend team/member/invite contracts, role-based team folder checks, generated-client adapters, Pinia actions, `TeamAuditPanel.vue`, and `WorkspaceView` handlers. |
| Team UI was still read-only after backend/client generation | Replaced the list-only panel with typed create/invite/member-role/remove emits and Naive UI controls using UnoCSS utilities. |
| Knowledge-base CRUD and interactive RAG UI were missing during TDD | Added backend knowledge-base/document/indexing contracts, regenerated the client, then wired workspace adapters, Pinia knowledge state/actions, `RagInsightPanel.vue`, and `WorkspaceView` handlers. |
| WorkspaceView initially did not pass RAG store refs/events into the panel | Added a view-level wiring test, then passed active knowledge-base id, documents, indexed files, loading flags, and create/select/add/ask handlers into `RagInsightPanel.vue`. |
| Workflow definition mutation and builder UI were missing during TDD | Added backend workflow create/update/validate/publish/execute contracts, regenerated the client, then wired workspace adapters, Pinia workflow state/actions, `AgentWorkflowPanel.vue`, and `WorkspaceView` handlers. |
| Vue Flow required explicit node `x`/`y` positions | Converted generated workflow `position` maps into typed `XYPosition` objects before passing nodes to Vue Flow. |
| Cross-resource RBAC was inconsistent after team folder permissions | Added shared backend file read/write helpers and applied them to listing, download, versions, update, copy, restore, delete, knowledge-base indexing, RAG citations, agent context files, and workflow execution. |
| Workflow execution tests assumed seed team-file access | Updated the workflow execution test to create a team and upload an accessible team file before executing. |
| Permission rule API/UI was missing during TDD | Added backend `/permissions/rules` schemas/routes/service logic, regenerated the OpenAPI client, then wired generated-client adapters, Pinia state/actions, `PermissionRulesPanel.vue`, and view/workbench events. |
| Strict TypeScript could not prove select option arrays were non-empty | Guarded local first-option constants in `PermissionRulesPanel.vue` before reading `.value`, avoiding unsafe `array[0]` assumptions in Vue component state setup. |
| Multipart upload routes were initially shadowed by dynamic file routes | Added static `/files/multipart-uploads...` routes before `/files/{file_id}` routes and covered init/chunk/status/complete behavior in backend tests. |
| Frontend full test run exposed stale architecture and component test fixtures | Removed stray `frontend/src/launch.json`, relaxed Vite proxy architecture assertions to check semantics instead of quote style, installed Pinia in `TeamAuditPanel` tests, and moved Naive UI input queries to explicit `data-testid` hooks. |
| File sharing behavior was missing after direct download support | Added `/files/{file_id}/share-links` and `/share-links/{token}/download`, capped share TTL at 3600 seconds, enforced password/download-count checks, and regenerated the frontend client. |
| Soft-delete recycle-bin behavior was missing during TDD | Added backend recycle-bin schemas/routes/service state, preserved file contents and versions across delete/restore, regenerated the OpenAPI client, and wired frontend adapter/store actions for loading and restoring deleted files. |
| `uv run pytest` did not resolve the backend package without `PYTHONPATH=.` | Used `PYTHONPATH=. uv run python -m pytest ...` for backend verification so tests import `app.main` consistently from `backend/`. |
| File updated-time range filtering was missing from FR-F07 | Added failing backend/store/component tests, then added typed backend datetime query params, inclusive service filtering, generated SDK regeneration, adapter/store filter fields, and FileWorkbench time inputs. |
| File annotation and reply behavior was missing during TDD | Added backend schemas/routes/service state, OpenAPI assertions, generated-client adapters, Pinia actions, `FileAnnotationPanel.vue`, and FileWorkbench/WorkspaceView event wiring. |
| Notification inbox behavior was missing during TDD | Added backend notification schemas/routes/service state, OpenAPI assertions, generated-client adapters, Pinia inbox actions, `NotificationInboxPanel.vue`, and TeamAuditPanel/WorkspaceView event wiring. |
| RAG broad-document prompts answer with “资料不足” despite indexed files | Current DB-backed RAG starts from query-to-chunk retrieval, stores no document-level context, and only applies full-document injection after a dominant-document citation pattern appears. Plan Phase 39 will add document profiles, intent-aware retrieval, and structured prompt assembly. |
| LLM planner introduced unstable agent tool choices during RAG verification | `AgentPlanner` now rejects LLM-added tools when fallback rules select direct answer, skips empty required parameters for non-fallback tools, and fills retained tool parameters from fallback extraction. |
| Default SQLite DB was locked during Phase 35 API reruns | Existing `uv run main.py` processes were holding `backend/whucs.db`, so Phase 35 API verification used an isolated temporary SQLite database instead of killing user-running processes. |
| Phase 36 detail UI needed denser execution context | `AgentTaskDetailPanel` and `AgentExecutionTimeline` now show compact history, message/tool/plan counts, total latency, history summaries, planned tools, retry metadata, and readable input/output summaries without adding another view-level state owner. |

## Latest Verification
- Final plan closure audit: no unchecked items remain in `task_plan.md` or `docs/superpowers/plans/2026-07-11-production-llm-agent-tool-flow.md`.
- Final backend full suite: initialized isolated SQLite DB with `app.models` + `init_db()`, then `DATABASE_URL=sqlite:///./test_full_final.db LLM_API_KEY= PYTHONPATH=. uv run python -m pytest -q` from `backend/` -> 126 passed, 3 warnings. The same full run against default `backend/whucs.db` hit a SQLite lock because existing `uv run main.py` processes were still running.
- Final frontend verification: `pnpm vitest run` -> 16 files passed, 78 tests passed; `pnpm type-check` -> passed; `pnpm build` -> passed.
- Final hygiene: `python3 -m json.tool .wolf/buglog.json >/dev/null` -> passed; `git diff --check` -> passed.
- Phase 36 workflow component tests: `pnpm vitest run src/components/workflow/__tests__/AgentTaskDetailPanel.spec.ts src/components/workflow/__tests__/AgentExecutionTimeline.spec.ts` -> 2 files passed, 3 tests passed.
- Phase 36 agent flow frontend tests: `pnpm vitest run src/stores/__tests__/agent.spec.ts src/components/workflow/__tests__/AgentTaskDetailPanel.spec.ts src/components/workflow/__tests__/AgentExecutionTimeline.spec.ts` -> 3 files passed, 8 tests passed.
- Phase 36 frontend build/type/hygiene: `pnpm type-check` -> passed; `pnpm build` -> passed; `git diff --check` -> passed.
- Phase 35 agent memory regression: `LLM_API_KEY= PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py::test_v2_agent_continue_persists_messages_and_summarizes_long_history -q` from `backend/` -> 1 passed, 3 warnings.
- Phase 35 isolated SQLite API checks: temp DB with initialized models, then `tests/test_workspace_api.py::test_agent_multi_turn_with_conversation_context`, calculator, multi-tool, missing-course-continue, and memory-summary tests -> 5 passed, 3 warnings.
- Phase 35 planner/executor/tool/OpenAPI checks: `LLM_API_KEY= PYTHONPATH=. uv run python -m pytest tests/test_agent_planner.py tests/test_agent_executor.py tests/test_tool_registry.py tests/test_openapi_export.py -q` -> 16 passed, 2 warnings.
- Phase 35 frontend/type/hygiene checks: `pnpm type-check` -> passed; `git diff --check` -> passed.
- Phase 39 RAG backend refactor: `LLM_API_KEY= PYTHONPATH=. uv run python -m pytest -q` from `backend/` -> 106 passed, 1 skipped, 3 warnings.
- Phase 39 focused RAG/API checks: `LLM_API_KEY= PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "v2_rag or kb_qa or knowledge_base_create_update_document_index_and_qa or parse_failure_on_garbage_binary or kb_document_indexing_uses_real_parser"` -> 7 passed, 56 deselected, 3 warnings.
- Phase 39 LLM/embedding checks: `LLM_API_KEY= PYTHONPATH=. uv run python -m pytest tests/test_llm.py tests/test_embedding.py -q` -> 16 passed.
- Phase 39 OpenAPI/client/type checks: `tests/test_openapi_export.py` -> 1 passed; `pnpm generate:client` -> passed; `pnpm type-check` -> passed; `git diff --check` -> passed.
- RAG/Agent refactor backend full suite after `RagPipeline` extraction and QA error-code handling: `PYTHONPATH=. uv run python -m pytest -q` from `backend/` -> 92 passed, 3 warnings.
- RAG/Agent refactor frontend unit tests: `pnpm vitest run` from `frontend/` -> 14 files passed, 67 tests passed.
- RAG/Agent refactor frontend type check: `pnpm type-check` -> passed.
- RAG/Agent refactor frontend build: `pnpm build` -> passed.
- RAG/Agent refactor hygiene: `python3 -m json.tool .wolf/buglog.json >/dev/null` and `git diff --check` -> passed.
- RAG focused checks: `PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "rag or qa or conversation"` -> 7 passed; `PYTHONPATH=. uv run python -m pytest tests/test_embedding.py tests/test_llm.py -q` -> 16 passed.
- WorkflowBuilderView direct debug fetch audit: `rg "fetch\\(" frontend/src/views/WorkflowBuilderView.vue` -> no matches.
- Backend focused notification/OpenAPI tests: `PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py::test_notifications_list_and_mark_read_for_invites_mentions_and_annotation_replies tests/test_workspace_api.py::test_team_file_annotations_support_replies_permissions_and_notifications tests/test_openapi_export.py -q` -> 3 passed, 1 Starlette/httpx deprecation warning.
- OpenAPI client generation: `pnpm generate:client` -> passed; generated schema/types include notification list/read contracts.
- Frontend focused notification tests: `pnpm vitest run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/NotificationInboxPanel.spec.ts src/components/workspace/__tests__/TeamAuditPanel.spec.ts -t notification` -> 3 files passed, 3 tests passed.
- Backend: `PYTHONPATH=. uv run python -m pytest -q` -> 31 passed, 1 Starlette/httpx deprecation warning.
- Frontend unit tests: `pnpm vitest run` -> 15 files passed, 60 tests passed.
- Frontend type check: `pnpm type-check` -> passed.
- Frontend build: `pnpm build` -> passed.
- OpenWolf bug log JSON: `python3 -m json.tool .wolf/buglog.json >/dev/null` -> passed.
- Diff hygiene: `git diff --check` -> passed.
- Backend focused annotation/OpenAPI tests: `PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k annotation` -> 1 passed, 28 deselected, 1 Starlette/httpx deprecation warning; `PYTHONPATH=. uv run python -m pytest tests/test_openapi_export.py -q` -> 1 passed.
- Frontend focused annotation tests: `pnpm vitest run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/FileAnnotationPanel.spec.ts -t annotation` -> 2 files passed, 2 tests passed, 18 skipped.
- Frontend workbench annotation tests: `pnpm vitest run src/components/workspace/__tests__/FileWorkbench.spec.ts src/components/workspace/__tests__/FileAnnotationPanel.spec.ts` -> 2 files passed, 6 tests passed.
- OpenAPI client generation: `pnpm generate:client` -> passed; generated schema/types include file annotation list/create/reply/delete contracts.
- Backend: `PYTHONPATH=. uv run python -m pytest -q` -> 30 passed, 1 Starlette/httpx deprecation warning.
- Frontend unit tests: `pnpm vitest run` -> 14 files passed, 57 tests passed.
- Frontend type check: `pnpm type-check` -> passed.
- Frontend build: `pnpm build` -> passed.
- OpenWolf bug log JSON: `python3 -m json.tool .wolf/buglog.json >/dev/null` -> passed.
- Diff hygiene: `git diff --check` -> passed.
- Backend focused updated-time filter test: `PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "updated_time_range"` -> 1 passed, 27 deselected, 1 Starlette/httpx deprecation warning.
- Frontend focused updated-time filter tests: `pnpm vitest run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/FileWorkbench.spec.ts -t "search"` -> 2 files passed, 2 tests passed, 20 skipped.
- OpenAPI client generation: `pnpm generate:client` -> passed; generated schema/types include `updated_from` and `updated_to`.
- Backend: `PYTHONPATH=. uv run python -m pytest -q` -> 29 passed, 1 Starlette/httpx deprecation warning.
- Frontend unit tests: `pnpm vitest run` -> 13 files passed, 54 tests passed.
- Frontend type check: `pnpm type-check` -> passed.
- Frontend build: `pnpm build` -> passed.
- OpenWolf bug log JSON: `python3 -m json.tool .wolf/buglog.json >/dev/null` -> passed.
- Diff hygiene: `git diff --check` -> passed.
- Backend parser tests: `PYTHONPATH=. uv run python -m pytest tests/test_parser.py -q` -> 21 passed.
- Backend parser integration tests: `PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "parser or parse_failure or segments"` -> 3 passed.
- Backend: `PYTHONPATH=. uv run python -m pytest -q` -> 66 passed, 1 Starlette/httpx deprecation warning.
- Frontend unit tests: `pnpm vitest run` -> 16 files passed, 62 tests passed.
- Frontend type check: `pnpm type-check` -> passed.
- Frontend build: `pnpm build` -> passed.
- OpenAPI client generation: `pnpm generate:client` -> passed.
- OpenWolf bug log JSON: `python3 -m json.tool .wolf/buglog.json >/dev/null` -> passed.
- Diff hygiene: `git diff --check` -> passed.

## Resources
- `report/requirements/requirements_specification.md`
- `report/design/system_design_specification.md`
- `DESIGN.md`
- `skills/whu-intelligent-file-workspace/SKILL.md`
- `frontend/package.json`
- `backend/pyproject.toml`

## Visual/Browser Findings
- No browser screenshots inspected yet.
