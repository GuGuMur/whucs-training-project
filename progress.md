# Progress Log

### 2026-07-16: Workflow execution kernel consolidation
- **Status:** in progress
- Extracted one `_execute_workflow_node()` path for tool, input/trigger, output, and passthrough nodes; formal execution and debug stepping now call the same implementation.
- Corrected list-workflows summaries to calculate actual node counts while still omitting full graph payloads.
- Added explicit formal/debug output parity coverage.
- Verification: workflow/OpenAPI slice 9 passed; frontend 27 files/109 tests and type-check passed; isolated full backend suite exited successfully; production build and Chromium E2E passed.
- **Status:** Phase 45 complete.

### 2026-07-16: Vue Flow production hardening
- **Status:** in progress
- Opened Phase 44 for optimistic concurrency, lossless edge metadata, and bounded debug-session lifecycle.
- Reloaded required Vue references and confirmed the changes stay within existing API/store/canvas boundaries.
- Added workflow revision tokens through domain/model/API/codec/store; stale updates return a structured 409 conflict.
- Added explicit edge label/type schema and normalized round-trip coverage.
- Added 30-minute debug expiry, cancellation API/client/store/UI, and post-cancel rejection coverage.
- Regenerated the OpenAPI client and updated SQLite compatibility/migration handling for workflow revisions.
- Final verification: frontend 27 files/109 tests passed, type-check and build passed; isolated full backend suite exited successfully; Chromium E2E passed; `git diff --check` passed.
- **Status:** Phase 44 complete.

### 2026-07-16: Vue Flow completion-definition closure
- **Status:** in progress
- Audited the original seven-stage plan after Phase 42 and found remaining gaps in undo/redo, unsaved-change protection, binding validation, version restore, and explicit execution inputs.
- Loaded the required planning and Vue core references and opened Phase 43 to close these gaps.
- Added bounded undo/redo graph history, drag checkpoints, toolbar controls, and unit/E2E coverage.
- Added unsaved-change confirmation for route exit, workflow switching, new workflow, template loading, and version restore.
- Added server-side binding/required-parameter validation and regression coverage for missing inputs and non-upstream references.
- Added version restore API/client/store/UI and an explicit workflow run-input panel.
- Final verification: backend workflow/OpenAPI slice 8 passed; isolated full backend suite exited successfully; frontend 27 files/109 tests passed; type-check and production build passed; Chromium authoring/undo/redo E2E passed; `git diff --check` passed.
- **Status:** Phase 43 complete; the Vue Flow completion definition is satisfied for supported node types (`input`, `trigger`, `tool`, `output`).

### 2026-07-16: Vue Flow core implementation
- **Status:** in progress
- Restored the implementation plan and reloaded all required Vue architecture references.
- Scope for this pass: workflow detail/publish contracts, single remote store, lossless graph codec, designer composable, and visible core canvas interaction.
- Added a failing backend regression test; initial result was HTTP 405 for missing workflow detail, confirming the audited contract gap.
- Added owner-scoped `GET /api/v2/workflows/{id}` and server-side publish validation; focused backend regression now passes.
- Regenerated the OpenAPI client and added the workflow-detail adapter/store action.
- Added a lossless workflow codec, typed `useWorkflowDesigner`, custom node handles, controlled canvas, toolbar and inspector.
- Rebuilt `/workflow` as “可视化编排 / 智能体任务” tabs with the visual designer as the primary surface and the dedicated workflow store as remote owner.
- Focused codec/designer/view tests: 3 files, 5 tests passed; frontend type-check passed after tightening Vue Flow node data typing.
- Backend v2 workflow/OpenAPI regression: 6 passed.
- Frontend full unit suite: 26 files, 104 tests passed.
- Frontend type-check and production build passed; `git diff --check` passed.
- **Status:** Phase 41 complete. Phase 42 remains for schema-aware parameters, immutable versions, published-only execution, real debug, and browser E2E.

### 2026-07-16: Vue Flow Phase 42 continuation
- **Status:** in progress
- Added a failing regression proving DB-backed v2 still executed drafts and debug returned simulated nodes.
- Implemented published-only execution/debug gates and real topological debug steps using workflow parameter resolution and ToolRegistry execution.
- Added frontend generated-client adapters/store lifecycle and a debug panel that advances real nodes and maps their status/output back to the canvas.
- Replaced raw tool parameter JSON with input-schema-driven binding editors; upstream output options are limited to graph ancestors and numeric literals preserve number types.
- Added workflow debug store and typed-binding tests.
- Verification: backend workflow/OpenAPI slice 7 passed; frontend full suite 27 files/106 tests passed; type-check and production build passed; isolated full backend suite exited successfully.
- Added `workflow_versions` and `workflow_executions` models, repositories, Alembic migration, domain schemas, and owner-scoped list APIs.
- Publishing now increments a semantic minor version and persists an immutable graph snapshot; editing a published workflow returns the live definition to draft without mutating its snapshot.
- Formal executions persist node-level history and version identity; the frontend store loads and refreshes both histories and renders them in `WorkflowHistoryPanel`.
- Replaced the obsolete starter E2E with a mocked-contract Chromium workflow authoring test and aligned Playwright with Vite port 8080/system Chrome.
- Final verification: frontend 27 files/107 tests passed, type-check passed, production build passed; Chromium E2E 1 passed; isolated full backend suite exited successfully; `git diff --check` passed.
- **Status:** Phase 42 complete.

### 2026-07-16: Vue Flow orchestration planning audit
- **Status:** in progress
- Loaded the required planning and Vue architecture skills and their mandatory references.
- Restored the long-running project plan and confirmed existing unrelated worktree changes.
- Located the current workflow view, workflow components, stores, generated API surface, and legacy workflow panel.
- No business code has been modified.
- Confirmed `/workflow` points to the full-page builder and that it bypasses the dedicated workflow Pinia store.
- Read the route-level graph model, client-side validation/serialization, drag/drop creation, save/execute behavior, workflow store, designer types, and router wiring.
- Audited the v2 backend workflow schema, persistence, validation, execution, debug implementation, permission tests, and frontend workflow tests.
- Completed the component map, seven implementation phases, acceptance criteria, and completion definition in `docs/superpowers/plans/2026-07-16-complete-vue-flow-orchestration.md`.
- **Status:** complete; business code remains unchanged.

## Session: 2026-07-08

### 2026-07-11: RAG backend document-level context audit
- **Status:** planning complete
- Actions taken:
  - Read existing planning state, RAG service, parser, LLM prompt service, DB-backed knowledge models/repositories, v2 knowledge API, and focused RAG tests.
  - Identified the live failure path: `WorkspaceServiceDB.answer_question()` relies on query-first chunk retrieval and only injects full text after citations already point strongly to one document.
  - Added Phase 39 to `task_plan.md` for a complete backend RAG refactor focused on document-level context planning.
  - Added findings documenting missing document profiles, parse-error masking, duplicated stream/non-stream context logic, and unstructured prompt inputs.
- Files modified:
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### 2026-07-11: RAG backend document-level context implementation
- **Status:** complete
- Actions taken:
  - Added a v2 regression test proving “讲解这些文档” with `top_k=1` still cites and covers all indexed documents in the knowledge base.
  - Extended knowledge documents with cleaned full text, summary, keywords, outline, char count, and token count, including Alembic and SQLite compatibility updates.
  - Added `RagPipeline.build_context()` with document-overview intent detection and document card context assembly.
  - Replaced `WorkspaceServiceDB`'s duplicated dominant-document full-text injection with the unified RAG context path for stream and non-stream Q&A.
  - Updated LLM prompts and fallback output for document-level explanation, including a filename preface when a real LLM rewrites source titles.
  - Hardened `AgentPlanner` normalization because full backend verification exposed LLM-generated empty-argument tool plans.
  - Regenerated the frontend OpenAPI client after extending `KnowledgeDocumentPublic`.
- Verification:
  - `LLM_API_KEY= PYTHONPATH=. uv run python -m pytest -q` from `backend/` -> 106 passed, 1 skipped, 3 warnings.
  - Focused RAG/API tests -> 7 passed, 56 deselected, 3 warnings.
  - `LLM_API_KEY= PYTHONPATH=. uv run python -m pytest tests/test_llm.py tests/test_embedding.py -q` -> 16 passed.
  - `PYTHONPATH=. uv run python -m pytest tests/test_openapi_export.py -q` -> 1 passed.
  - `pnpm generate:client` -> passed.
  - `pnpm type-check` -> passed.
  - `git diff --check` -> passed.
- Files modified:
  - `backend/app/services/rag_pipeline.py`
  - `backend/app/services/workspace_db.py`
  - `backend/app/services/llm.py`
  - `backend/app/services/agent_planner.py`
  - `backend/app/models/knowledge.py`
  - `backend/app/domain/knowledge.py`
  - `backend/app/repositories/knowledge.py`
  - `backend/app/core/database.py`
  - `backend/alembic/versions/20260711_rag_agent_refactor.py`
  - `backend/tests/test_workspace_api.py`
  - `frontend/src/client/openapi/workspace.openapi.json`
  - `frontend/src/client/generated/*`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 1: Requirements & Current-State Discovery
- **Status:** complete
- **Started:** 2026-07-08 08:26
- Actions taken:
  - Loaded required workflow skills and OpenWolf project instructions.
  - Read report requirement/design sections covering MVP scope, API paths, UI layout, and architecture.
  - Inspected current framework state for `frontend/package.json` and `backend/pyproject.toml`.
  - Created persistent planning files for this long-running goal.
- Files created/modified:
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 2: MVP Architecture Skeleton
- **Status:** complete
- Actions taken:
  - Wrote backend API contract tests first.
  - Confirmed tests fail because `app.main` is missing after dependencies are provided through `uv run --no-project`.
  - Added a modular FastAPI package with typed schemas, route layer, and deterministic in-memory workspace service.
  - Ran backend contract tests successfully.
- Files created/modified:
  - `backend/tests/test_workspace_api.py`
  - `backend/app/main.py`
  - `backend/app/api/routes.py`
  - `backend/app/domain/schemas.py`
  - `backend/app/services/workspace.py`
  - `backend/main.py`

### Phase 3: Vue Workbench Shell
- **Status:** complete
- Actions taken:
  - Added a report-aligned Chinese workspace route as the root screen.
  - Added a typed workspace API client, deterministic demo data, and a Pinia workspace store.
  - Added Naive UI + UnoCSS workbench components for summary metrics, file table, RAG citations, agent/tool timeline, workflow template, teams, and audit logs.
  - Added a frontend blackbox test for the critical rendered states.
  - Removed stale Vue starter screens/tests after replacing the starter app.
- Files created/modified:
  - `frontend/uno.config.ts`
  - `frontend/src/App.vue`
  - `frontend/src/main.ts`
  - `frontend/src/router/index.ts`
  - `frontend/src/services/workspaceApi.ts`
  - `frontend/src/stores/workspace.ts`
  - `frontend/src/views/WorkspaceView.vue`
  - `frontend/src/views/__tests__/WorkspaceView.spec.ts`
  - `frontend/src/components/workspace/*.vue`
  - `frontend/src/assets/base.css`
  - `frontend/src/assets/main.css`
  - `frontend/index.html`

### Phase 4: Integration & Verification
- **Status:** complete
- Actions taken:
  - Ran backend API contract tests from `backend/` using `uv run --no-project`.
  - Ran frontend unit tests, type checking, and production build from `frontend/`.
  - Started the Vite dev server at `http://127.0.0.1:5173/`.
  - Inspected desktop and mobile viewports in browser devtools; fixed text overlap and mobile horizontal overflow.
  - Confirmed browser console has no errors/warnings/issues after reload.
- Files created/modified:
  - `task_plan.md`
  - `progress.md`
  - `.wolf/anatomy.md`
  - `.wolf/memory.md`
  - `.wolf/cerebrum.md`
  - `.wolf/buglog.json`

### Phase 5: DESIGN.md Compliance Pass
- **Status:** complete
- Actions taken:
  - Re-read `DESIGN.md` and adjusted the frontend toward a calm academic workbench: restrained blue, neutral surfaces, semantic status colors, and purple only for AI/RAG indicators.
  - Added icons to major commands, decorative icon `aria-hidden` attributes, section scroll offsets for sticky mobile navigation, and status-aware agent timeline coloring.
  - Replaced the phone file table with grouped mobile rows while preserving `NDataTable` for wider screens.
  - Rechecked desktop and phone viewports in browser devtools.
- Files modified:
  - `frontend/src/App.vue`
  - `frontend/src/assets/base.css`
  - `frontend/src/views/WorkspaceView.vue`
  - `frontend/src/components/workspace/StatusChip.vue`
  - `frontend/src/components/workspace/FileWorkbench.vue`
  - `frontend/src/components/workspace/RagInsightPanel.vue`
  - `frontend/src/components/workspace/AgentWorkflowPanel.vue`
  - `frontend/src/components/workspace/TeamAuditPanel.vue`

### Phase 6: Frontend Architecture Restructure
- **Status:** complete
- Actions taken:
  - Added a failing architecture test for the agreed frontend source boundaries.
  - Replaced `src/services/` with `src/client/` as the temporary API/client boundary and added `src/auth/` for auth/session helpers that can later integrate with generated client calls.
  - Added `src/plugins/` for Pinia/router/Naive UI installation and Naive theme overrides.
  - Added `src/composables/` for workspace navigation and viewport layout selection.
  - Split `src/layouts/` into `DesktopWorkspaceLayout.vue` and `MobileWorkspaceLayout.vue`; kept page composition in `src/views/WorkspaceView.vue`.
  - Removed unused Vue starter logo/icon files and empty starter test directories.
- Files created/modified:
  - `frontend/src/auth/index.ts`
  - `frontend/src/auth/workspaceAccess.ts`
  - `frontend/src/client/index.ts`
  - `frontend/src/client/workspace.ts`
  - `frontend/src/composables/useWorkspaceLayoutMode.ts`
  - `frontend/src/composables/useWorkspaceNavigation.ts`
  - `frontend/src/layouts/DesktopWorkspaceLayout.vue`
  - `frontend/src/layouts/MobileWorkspaceLayout.vue`
  - `frontend/src/plugins/index.ts`
  - `frontend/src/plugins/naive.ts`
  - `frontend/tests/frontendArchitecture.spec.ts`
  - `frontend/src/App.vue`
  - `frontend/src/main.ts`
  - `frontend/src/views/WorkspaceView.vue`
  - `frontend/src/stores/workspace.ts`

### Phase 7: Auth Session and Protected Routing
- **Status:** complete
- Actions taken:
  - Added focused tests for auth store login/register/session restoration, route guard redirects, and the login/register view.
  - Added `src/stores/auth.ts` as the Pinia auth state owner, using generated OpenAPI SDK calls for `/auth/login`, `/auth/register`, and `/users/me`.
  - Extended `src/auth/workspaceAccess.ts` with localStorage persistence and generated-client-compatible `authorization` headers.
  - Changed the root route into a protected workspace route and added guest-only `/login` via return-based Vue Router guards.
  - Added `src/views/LoginView.vue` under `views/` with Naive UI form controls, JWT/RBAC/audit copy, and login/register modes.
  - Linked `src/stores/workspace.ts` to the auth session token while preserving demo fallback behavior.
- Files created/modified:
  - `frontend/src/stores/auth.ts`
  - `frontend/src/stores/__tests__/auth.spec.ts`
  - `frontend/src/views/LoginView.vue`
  - `frontend/src/views/__tests__/LoginView.spec.ts`
  - `frontend/src/router/index.ts`
  - `frontend/src/router/__tests__/authGuard.spec.ts`
  - `frontend/src/auth/workspaceAccess.ts`
  - `frontend/src/stores/workspace.ts`

### Phase 8: Refresh Session Boundary Hardening
- **Status:** complete
- Actions taken:
  - Added backend TDD coverage for refresh token rotation, refresh-token-only refresh access, and access-token-only protected resource access.
  - Added `RefreshTokenRequest`, `POST /api/v1/auth/refresh`, and `WorkspaceService.refresh_session()`.
  - Added a random token `jti` so refreshed access and refresh tokens are distinct from the prior issued pair.
  - Added frontend auth-store coverage and `refreshSession()` using `refreshApiV1AuthRefreshPost` from the generated SDK.
  - Regenerated the OpenAPI client after the backend schema changed.
- Files created/modified:
  - `backend/tests/test_workspace_api.py`
  - `backend/app/domain/schemas.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/workspace.py`
  - `frontend/src/stores/auth.ts`
  - `frontend/src/stores/__tests__/auth.spec.ts`
  - `frontend/src/client/openapi/workspace.openapi.json`
  - `frontend/src/client/generated/*`

### Phase 9: User Profile Maintenance
- **Status:** complete
- Actions taken:
  - Added backend TDD coverage for current-user profile updates and duplicate-email rejection.
  - Added `UserUpdate`, `PATCH /api/v1/users/me`, `WorkspaceService.update_user_profile()`, email index maintenance, and profile-update audit logging.
  - Regenerated the OpenAPI client so frontend code uses `updateMeApiV1UsersMePatch`.
  - Added `auth.updateProfile()` in the Pinia auth store, preserving session persistence in `src/auth/`.
  - Added protected `/profile` route and `ProfileView.vue` under `views/` with Naive UI form controls and UnoCSS utilities.
  - Added a workbench top-bar profile entry in both desktop and mobile layouts.
- Files created/modified:
  - `backend/tests/test_workspace_api.py`
  - `backend/app/domain/schemas.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/workspace.py`
  - `frontend/src/client/openapi/workspace.openapi.json`
  - `frontend/src/client/generated/*`
  - `frontend/src/stores/auth.ts`
  - `frontend/src/stores/__tests__/auth.spec.ts`
  - `frontend/src/router/index.ts`
  - `frontend/src/router/__tests__/authGuard.spec.ts`
  - `frontend/src/views/ProfileView.vue`
  - `frontend/src/views/__tests__/ProfileView.spec.ts`
  - `frontend/src/layouts/DesktopWorkspaceLayout.vue`
  - `frontend/src/layouts/MobileWorkspaceLayout.vue`

### Phase 12: File Download & Delete Actions
- **Status:** complete
- Actions taken:
  - Added backend TDD coverage for uploaded-file download, delete, repeat-delete 404, and file audit events.
  - Added in-memory file content storage, `WorkspaceService.download_file()`, `WorkspaceService.delete_file()`, and FastAPI download/delete routes.
  - Regenerated the OpenAPI client so `deleteFileApiV1FilesFileIdDelete` and `downloadFileApiV1FilesFileIdDownloadGet` are available under `src/client/generated/`.
  - Added `downloadWorkspaceFile()` and `deleteWorkspaceFile()` in `src/client/workspace.ts`, keeping auth headers in `src/auth/`.
  - Added `downloadFile()` and `deleteFile()` actions plus per-file loading state in `stores/workspace.ts`.
  - Added Naive UI row controls in `FileWorkbench.vue` and kept `WorkspaceView.vue` as a composition layer that saves downloaded blobs.
- Files created/modified:
  - `backend/tests/test_workspace_api.py`
  - `backend/tests/test_openapi_export.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/workspace.py`
  - `frontend/src/client/openapi/workspace.openapi.json`
  - `frontend/src/client/generated/*`
  - `frontend/src/client/workspace.ts`
  - `frontend/src/stores/workspace.ts`
  - `frontend/src/stores/__tests__/workspace.spec.ts`
  - `frontend/src/components/workspace/FileWorkbench.vue`
  - `frontend/src/components/workspace/__tests__/FileWorkbench.spec.ts`
  - `frontend/src/views/WorkspaceView.vue`

### Phase 13: File Search & Upload UI
- **Status:** complete
- Actions taken:
  - Added frontend TDD coverage for file listing/upload adapter calls and FileWorkbench search/upload emits.
  - Added `listWorkspaceFiles()` and `uploadWorkspaceFile()` wrappers around generated `filesApiV1FilesGet` and `uploadFileApiV1FilesUploadPost`.
  - Added workspace store state/actions for active file filters, file-list loading, upload loading, and snapshot updates after filtered list or uploaded file responses.
  - Added a Naive UI search toolbar for filename/tag/type filtering and a compact UnoCSS upload panel for file/folder/tags input.
  - Kept API/session boundaries intact: auth headers come from `src/auth/`, generated SDK stays in `src/client/generated/`, state stays in `stores/`, and route orchestration stays in `views/WorkspaceView.vue`.
- Files created/modified:
  - `frontend/src/client/workspace.ts`
  - `frontend/src/stores/workspace.ts`
  - `frontend/src/stores/__tests__/workspace.spec.ts`
  - `frontend/src/components/workspace/FileWorkbench.vue`
  - `frontend/src/components/workspace/FileUploadPanel.vue`
  - `frontend/src/components/workspace/__tests__/FileWorkbench.spec.ts`
  - `frontend/src/views/WorkspaceView.vue`

### Phase 14: Folder CRUD Tree & Breadcrumb UI
- **Status:** complete
- Actions taken:
  - Added backend TDD coverage for FR-F02 folder CRUD, including nested tree creation, move, delete, non-empty delete rejection, root protection, cycle rejection, and folder audit events.
  - Added `FolderCreate`/`FolderUpdate`, folder routes, and in-memory folder service mutations with stable OpenAPI paths.
  - Regenerated the OpenAPI client and added generated-client-backed folder adapters in `src/client/workspace.ts`.
  - Added workspace store folder tree state/actions, active folder selection, folder options, and dynamic upload destination options.
  - Added `FolderTreePanel.vue` with Naive UI controls for tree navigation, breadcrumbs, create, rename, move, and delete, then composed it inside `FileWorkbench.vue`.
  - Updated `frontend/package.json` so OpenAPI export uses `python3` in the backend `uv` command.
- Files created/modified:
  - `backend/tests/test_workspace_api.py`
  - `backend/tests/test_openapi_export.py`
  - `backend/app/domain/schemas.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/workspace.py`
  - `frontend/package.json`
  - `frontend/src/client/openapi/workspace.openapi.json`
  - `frontend/src/client/generated/*`
  - `frontend/src/client/workspace.ts`
  - `frontend/src/stores/workspace.ts`
  - `frontend/src/stores/__tests__/workspace.spec.ts`
  - `frontend/src/components/workspace/FolderTreePanel.vue`
  - `frontend/src/components/workspace/FileWorkbench.vue`
  - `frontend/src/components/workspace/FileUploadPanel.vue`
  - `frontend/src/components/workspace/__tests__/FolderTreePanel.spec.ts`
  - `frontend/src/views/WorkspaceView.vue`

### Phase 15: File Lifecycle Move Copy & Version UI
- **Status:** complete
- Actions taken:
  - Selected the next report-aligned slice after folder CRUD: FR-F01 file rename/move/copy/tag update and FR-F05 same-name upload versioning/version restore.
  - Confirmed the design report lists `PATCH /files/{file_id}`, `GET /files/{file_id}/versions`, and version restore routes; copy is required by FR-F01 and will use `POST /files/{file_id}/copy`.
  - Added backend failing tests for file update/copy/folder validation, same-name upload versioning, restore, audit events, and OpenAPI path export.
  - Verified red state with `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest tests/test_workspace_api.py::test_file_update_copy_and_folder_validation_are_audited tests/test_workspace_api.py::test_same_name_upload_creates_versions_and_restore_creates_new_current_version tests/test_openapi_export.py::test_export_openapi_writes_workspace_contract -q`: `3 failed`, expected 405/missing OpenAPI route/new-file-on-same-name failures.
  - Added backend file lifecycle schemas, routes, in-memory version tracking, same-name upload versioning, file update/copy/restore service methods, folder-scope validation, and audit events.
  - Re-ran the focused backend tests: `3 passed, 1 warning`.
  - Ran full backend tests with `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest -q`: `17 passed, 1 warning`.
  - Regenerated the frontend OpenAPI client with `cd frontend && pnpm generate:client`; hey-api generated 4 files under `src/client/generated/`.
  - Added frontend failing tests for generated-client-backed update/copy/version/restore store actions and FileWorkbench lifecycle panel events.
  - Verified red state with `cd frontend && pnpm test:unit --run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/FileWorkbench.spec.ts`: `4 failed`, expected missing adapter/action/UI failures.
  - Added generated-client-backed lifecycle adapters in `src/client/workspace.ts` for update, copy, list versions, and restore.
  - Added Pinia workspace lifecycle actions and loading state for file update/copy/version loading/version restore while keeping auth headers in `src/auth/`.
  - Added `FileLifecyclePanel.vue` as a focused Naive UI + UnoCSS presenter for rename, move, tags, copy, and version rollback.
  - Wired lifecycle props/events through `FileWorkbench.vue` and `WorkspaceView.vue`, keeping page orchestration in `views/`.
  - Re-ran focused frontend tests: `2 passed, 15 tests passed`.
  - Re-ran full frontend tests, type checking, production build, full backend tests, JSON validation, and diff whitespace checks.
- Files created/modified:
  - `task_plan.md`
  - `progress.md`
  - `backend/tests/test_workspace_api.py`
  - `backend/tests/test_openapi_export.py`
  - `backend/app/domain/schemas.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/workspace.py`
  - `frontend/src/client/generated/*`
  - `frontend/src/client/openapi/workspace.openapi.json`
  - `frontend/src/client/workspace.ts`
  - `frontend/src/stores/workspace.ts`
  - `frontend/src/stores/__tests__/workspace.spec.ts`
  - `frontend/src/components/workspace/FileLifecyclePanel.vue`
  - `frontend/src/components/workspace/FileWorkbench.vue`
  - `frontend/src/components/workspace/__tests__/FileWorkbench.spec.ts`
  - `frontend/src/views/WorkspaceView.vue`

### Phase 16: Team Membership Invites & Folder Permission Boundary
- **Status:** complete
- Actions taken:
  - Selected the next report-aligned collaboration slice: FR-C01/C02/C03 team membership/invites, FR-C08 audit logging, and FR-C10 team-folder permission boundaries.
  - Added backend failing tests for team creation, invites, member role updates/removal, audit events, guest read-only team-folder behavior, and member write access.
  - Verified backend red state with `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest tests/test_workspace_api.py::test_team_invites_role_updates_and_removal_are_audited tests/test_workspace_api.py::test_team_folder_permissions_enforce_guest_read_only_and_member_write tests/test_openapi_export.py::test_export_openapi_writes_workspace_contract -q`: `3 failed`, expected missing team POST/routes.
  - Added backend team schemas, in-memory team/member/invite state, team CRUD/member routes, user-aware team listing/snapshot behavior, and role-based folder read/write checks.
  - Re-ran the focused backend tests: `3 passed, 1 warning`.
  - Regenerated the frontend OpenAPI client with `cd frontend && pnpm generate:client`; hey-api generated 4 files under `src/client/generated/`.
  - Added frontend failing tests for generated-client-backed team store actions and TeamAuditPanel creation/invite/member controls.
  - Verified frontend red state with `cd frontend && pnpm test:unit --run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/TeamAuditPanel.spec.ts`: `3 failed`, expected missing team-summary helper and missing panel controls.
  - Added generated-client-backed team adapters in `src/client/workspace.ts` for list/create/detail/invite/join/update/remove.
  - Added Pinia workspace team state/actions for active team detail, team operation loading, create, detail load, invite, join, role update, and member removal.
  - Replaced the read-only `TeamAuditPanel.vue` with a Naive UI + UnoCSS presenter for team creation, opening team detail, inviting members, updating member roles, removing members, and audit display.
  - Wired team props/events through `WorkspaceView.vue`, keeping page orchestration in `views/` and session ownership in `auth/`.
  - Re-ran focused frontend tests: `2 passed, 14 tests passed`.
  - Re-ran full frontend tests, type checking, production build, full backend tests, JSON validation, and diff whitespace checks.
- Files created/modified:
  - `backend/tests/test_workspace_api.py`
  - `backend/tests/test_openapi_export.py`
  - `backend/app/domain/schemas.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/workspace.py`
  - `frontend/src/client/generated/*`
  - `frontend/src/client/openapi/workspace.openapi.json`
  - `frontend/src/client/workspace.ts`
  - `frontend/src/stores/workspace.ts`
  - `frontend/src/stores/__tests__/workspace.spec.ts`
  - `frontend/src/components/workspace/TeamAuditPanel.vue`
  - `frontend/src/components/workspace/__tests__/TeamAuditPanel.spec.ts`
  - `frontend/src/views/WorkspaceView.vue`

### Phase 17: Knowledge Base CRUD & Interactive RAG Panel
- **Status:** complete
- Actions taken:
  - Selected the next report-aligned RAG slice: knowledge-base CRUD, document indexing, deterministic retrieval, cited QA, and an interactive knowledge panel.
  - Added backend tests for knowledge-base create/update, document indexing, audited QA citations, and OpenAPI path export.
  - Verified backend RED state before implementation in the prior run: missing `/knowledge-bases` routes and OpenAPI paths.
  - Added backend knowledge-base schemas, in-memory knowledge-base/document/chunk state, deterministic chunking/retrieval, document indexing service methods, routes, seed data, snapshot summary updates, and QA citation behavior.
  - Re-ran focused backend tests: `3 passed, 1 warning`.
  - Regenerated the frontend OpenAPI client with `cd frontend && pnpm generate:client`; hey-api generated 4 files under `src/client/generated/`.
  - Added frontend tests for generated-client-backed knowledge-base store actions, `RagInsightPanel.vue` create/select/add-document/ask emits, citations, indexed document status, and `WorkspaceView.vue` RAG wiring.
  - Verified frontend RED states: missing knowledge-base adapters/actions/interactive panel, then missing `WorkspaceView` props/events for the RAG panel.
  - Added generated-client-backed knowledge-base adapters in `src/client/workspace.ts` for list/create/update/documents/add-document/question.
  - Added Pinia workspace knowledge-base state/actions for active knowledge base, document lists, create, document load/add, file knowledge-base markers, and QA answer/citation updates.
  - Replaced the read-only `RagInsightPanel.vue` with a Naive UI + UnoCSS presenter for knowledge-base creation, document indexing, question input, answers, and citations.
  - Wired RAG props/events through `WorkspaceView.vue`, keeping the view as a composition layer and keeping auth/session ownership in `auth/`.
  - Re-ran focused frontend tests: `3 passed, 17 tests passed`.
  - Re-ran frontend type checking, full frontend tests, production build, full backend tests, and OpenAPI client generation.
- Files created/modified:
  - `backend/tests/test_workspace_api.py`
  - `backend/tests/test_openapi_export.py`
  - `backend/app/domain/schemas.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/workspace.py`
  - `frontend/src/client/generated/*`
  - `frontend/src/client/openapi/workspace.openapi.json`
  - `frontend/src/client/workspace.ts`
  - `frontend/src/stores/workspace.ts`
  - `frontend/src/stores/__tests__/workspace.spec.ts`
  - `frontend/src/components/workspace/RagInsightPanel.vue`
  - `frontend/src/components/workspace/__tests__/RagInsightPanel.spec.ts`
  - `frontend/src/views/WorkspaceView.vue`
  - `frontend/src/views/__tests__/WorkspaceView.spec.ts`
  - `task_plan.md`
  - `progress.md`
  - `findings.md`

### Phase 18: Editable Workflow Definitions & Builder UI
- **Status:** complete
- Actions taken:
  - Selected the next report-aligned workflow slice: editable workflow definitions, DAG validation, publication, deterministic execution, and a workflow-builder UI.
  - Added backend tests for workflow create/update/validate/publish/execute behavior plus OpenAPI path export.
  - Verified backend RED state before implementation: `POST /api/v1/workflows` returned 405 and OpenAPI lacked the new workflow mutation paths.
  - Added backend workflow create/update/validate/publish routes, in-memory `StoredWorkflow` state, DAG validation, topological execution order, seed workflow nodes/edges, execution node outputs, and audit logging.
  - Re-ran focused backend tests: `3 passed, 1 warning`.
  - Regenerated the frontend OpenAPI client with `cd frontend && pnpm generate:client`; hey-api generated workflow SDK functions and types.
  - Added frontend tests for generated-client-backed workflow store actions, `AgentWorkflowPanel.vue` create/select/save/validate/publish/execute emits, Vue Flow canvas rendering, validation state, and `WorkspaceView.vue` workflow wiring.
  - Verified frontend RED states: missing workflow adapters/actions, old read-only workflow panel, and missing `WorkspaceView` workflow props/events.
  - Added generated-client-backed workflow adapters in `src/client/workspace.ts` for list/create/update/validate/publish/execute and extended demo workflow nodes/edges.
  - Added Pinia workspace workflow state/actions for active workflow, validation, publication, execution, loading, and execution-to-agent-timeline updates.
  - Replaced the read-only `AgentWorkflowPanel.vue` with a Naive UI + UnoCSS workflow builder panel using Vue Flow for node/edge preview.
  - Wired workflow props/events through `WorkspaceView.vue`, keeping the view as a composition layer and keeping auth/session ownership in `auth/`.
  - Re-ran focused frontend tests: `3 passed, 19 tests passed`.
  - Re-ran frontend type checking, full frontend tests, production build, and full backend tests.
- Files created/modified:
  - `backend/tests/test_workspace_api.py`
  - `backend/tests/test_openapi_export.py`
  - `backend/app/domain/schemas.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/workspace.py`
  - `frontend/src/client/generated/*`
  - `frontend/src/client/openapi/workspace.openapi.json`
  - `frontend/src/client/workspace.ts`
  - `frontend/src/stores/workspace.ts`
  - `frontend/src/stores/__tests__/workspace.spec.ts`
  - `frontend/src/components/workspace/AgentWorkflowPanel.vue`
  - `frontend/src/components/workspace/__tests__/AgentWorkflowPanel.spec.ts`
  - `frontend/src/views/WorkspaceView.vue`
  - `frontend/src/views/__tests__/WorkspaceView.spec.ts`
  - `task_plan.md`
  - `progress.md`
  - `findings.md`

### Phase 19: Cross-Resource RBAC Enforcement
- **Status:** complete
- Actions taken:
  - Selected a narrow RBAC hardening slice instead of a full ACL editor: enforce existing team roles across file, knowledge, agent, and workflow runtime paths.
  - Added a backend red test covering team-file search visibility, outsider download denial, guest read-only behavior, guest write/delete denial, unauthorized knowledge-base document indexing, and unauthorized workflow execution.
  - Verified RED state with `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest tests/test_workspace_api.py::test_team_file_read_and_write_permissions_are_enforced_across_resources -q`: failed because an outsider could still find the team file in `/api/v1/files`.
  - Passed the authenticated user into file listing and added shared file read/write permission checks in the workspace service.
  - Applied the read/write checks to file listing, download, versions, update, copy, restore, delete, knowledge-base document indexing, RAG citation filtering, agent context files, and workflow execution.
  - Updated the workflow execution test to create a team and upload a team file under the current owner before executing, instead of relying on seed-team access.
  - Re-ran the focused RBAC test and full backend test suite.
- Files created/modified:
  - `backend/tests/test_workspace_api.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/workspace.py`
  - `task_plan.md`
  - `progress.md`
  - `findings.md`

### Phase 20: Resource ACL Rules & Permission Panel
- **Status:** complete
- Actions taken:
  - Selected the next report-aligned security slice: FR-C08 resource-level permission modes, FR-C09 inheritance/overrides, and FR-C10 permission-change audit events.
  - Scoped the phase to file/folder resources and team/user subjects so it builds directly on Phase 19 shared RBAC checks without expanding into the full admin backend or persistent repository layer yet.
  - Added backend coverage and implementation for permission rule list/create/delete, explicit deny precedence, inherited folder rules, file-level overrides, and permission-change audit events.
  - Exposed `/api/v1/permissions/rules` and `/api/v1/permissions/rules/{rule_id}` in the FastAPI/OpenAPI contract with typed subject/resource/action/effect schemas.
  - Regenerated the frontend OpenAPI client with `pnpm generate:client`; generated SDK names include `permissionRulesApiV1PermissionsRulesGet`, `createPermissionRuleApiV1PermissionsRulesPost`, and `deletePermissionRuleApiV1PermissionsRulesRuleIdDelete`.
  - Added generated-client-backed permission adapters in `src/client/workspace.ts`, Pinia permission-rule state/actions in `stores/workspace.ts`, and the Naive UI + UnoCSS `PermissionRulesPanel.vue` presenter.
  - Wired permission-rule props/events through `FileWorkbench.vue` and `WorkspaceView.vue` while keeping `services/` deleted and auth headers owned by `src/auth/`.
  - Re-ran focused frontend permission tests, full frontend tests, type checking, production build, full backend tests, JSON validation, services-boundary check, and diff whitespace check.
- Files created/modified:
  - `backend/tests/test_workspace_api.py`
  - `backend/tests/test_openapi_export.py`
  - `backend/app/domain/schemas.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/workspace.py`
  - `frontend/src/client/openapi/workspace.openapi.json`
  - `frontend/src/client/generated/*`
  - `frontend/src/client/workspace.ts`
  - `frontend/src/stores/workspace.ts`
  - `frontend/src/stores/__tests__/workspace.spec.ts`
  - `frontend/src/components/workspace/PermissionRulesPanel.vue`
  - `frontend/src/components/workspace/__tests__/PermissionRulesPanel.spec.ts`
  - `frontend/src/components/workspace/FileWorkbench.vue`
  - `frontend/src/views/WorkspaceView.vue`
  - `frontend/src/views/__tests__/WorkspaceView.spec.ts`
  - `task_plan.md`
  - `progress.md`
  - `findings.md`

### Phase 21: Remote Merge — Full-Page Views & Guest Auth
- **Status:** complete
- Actions taken:
  - Committed all local changes (Phases 14-20) to `local-wip` branch.
  - Pulled 14 remote commits from `origin/main` (fast-forward): `permission-backend`, `frontend` branches merged.
  - Merged `local-wip` into updated `main`, resolving 6 conflicted files.
  - Resolved backend conflicts: kept comprehensive local-wip implementations (lockout, folder CRUD, file lifecycle, team membership, knowledge bases, workflows, RBAC, ACL rules) over simpler remote versions.
  - Resolved `AgentWorkflowPanel.vue`: merged remote's RouterLink to `/workflow` with local-wip's validation NTag.
  - Resolved `RagInsightPanel.vue`: kept interactive KB CRUD panel from local-wip over remote's simpler view.
  - Resolved `vite.config.ts`: kept local-wip's visualizer, manualChunks, and port 8080 config.
  - Documented remote contributions in findings.md, task_plan.md, and progress.md.
- Files created by remote:
  - `frontend/src/views/WorkflowBuilderView.vue` — drag/drop Vue Flow orchestration (637 lines)
  - `frontend/src/views/TeamChatView.vue` — team collab chat with @mentions (437 lines)
  - `frontend/src/views/RagQaView.vue` — standalone RAG Q&A page (168 lines)
  - `frontend/src/views/PermissionAuditView.vue` — admin-only audit (306 lines)
  - `.vscode/launch.json`, `.vscode/tasks.json`, `frontend/.vscode/extensions.json`, `frontend/src/launch.json`
- Files modified by remote:
  - `frontend/src/router/index.ts` — added `/rag`, `/workflow`, `/team-chat`, `/permission-audit` routes with `requiresAdmin` guard
  - `frontend/src/stores/auth.ts` — added guest login, `selectedAccessRole`, `canAccessPermissionAudit`
  - `frontend/src/views/LoginView.vue` — guest role switching
  - `frontend/src/layouts/DesktopWorkspaceLayout.vue` — new nav items
  - `frontend/src/layouts/MobileWorkspaceLayout.vue` — new nav items
  - `frontend/src/composables/useWorkspaceNavigation.ts` — nav for new pages
  - `frontend/src/components/workspace/TeamAuditPanel.vue` — collaboration updates
  - `frontend/src/components/workspace/AgentWorkflowPanel.vue` — RouterLink to `/workflow`
  - `frontend/src/components/workspace/RagInsightPanel.vue` — RouterLink to `/rag`
  - `backend/app/api/routes.py` — permission routes (merged)
  - `backend/app/domain/schemas.py` — permission schemas (merged)
  - `backend/app/services/workspace.py` — `_seed_demo_user`, permission backend (merged)

### Phase 24: Notification Inbox API/UI
- **Status:** complete
- Actions taken:
  - Added backend notification schemas, in-memory notification entities, list/read service methods, and `/api/v1/notifications` routes.
  - Created notification records for team invites to existing users, annotation mentions, annotation replies, and workflow completion on team files.
  - Changed workspace/team unread counts to derive from unread notification entities for the current user.
  - Regenerated the OpenAPI client and added notification adapters/state/actions in `frontend/src/client/workspace.ts` and `frontend/src/stores/workspace.ts`.
  - Added `NotificationInboxPanel.vue` and wired it into `TeamAuditPanel.vue` and `WorkspaceView.vue`.
  - Verified focused notification behavior plus full backend/frontend suites, type checking, build, JSON validation, and diff whitespace.
- Files created/modified:
  - `backend/app/domain/schemas.py`
  - `backend/app/api/routes.py`
  - `backend/app/services/workspace.py`
  - `backend/tests/test_workspace_api.py`
  - `backend/tests/test_openapi_export.py`
  - `frontend/src/client/openapi/workspace.openapi.json`
  - `frontend/src/client/generated/*`
  - `frontend/src/client/workspace.ts`
  - `frontend/src/stores/workspace.ts`
  - `frontend/src/stores/__tests__/workspace.spec.ts`
  - `frontend/src/components/workspace/NotificationInboxPanel.vue`
  - `frontend/src/components/workspace/__tests__/NotificationInboxPanel.spec.ts`
  - `frontend/src/components/workspace/TeamAuditPanel.vue`
  - `frontend/src/components/workspace/__tests__/TeamAuditPanel.spec.ts`
  - `frontend/src/views/WorkspaceView.vue`

### Phase 25: Document Parser Integration & Verification
- **Status:** complete
- Actions taken:
  - Removed dead `_chunk_file_content()` from workspace.py (replaced by `parse_document()`).
  - Added `backend/tests/test_parser.py` with 21 unit tests covering all 6 formats (PDF/DOCX/PPTX/TXT/MD/CSV), format detection, error handling, and segment metadata.
  - All 31 existing API tests pass without modification.
  - Added 3 parser integration tests: KB indexing uses real parser, parse failure marks file failed, QA citations come from parsed segments.
  - Regenerated OpenAPI client and verified frontend parse_status display.
  - Full verification: 56 backend tests, 16 frontend files (62 tests), type check, build all pass.
- Files created/modified:
  - `backend/tests/test_parser.py` (NEW)
  - `backend/app/services/workspace.py` (removed dead code)
  - `backend/tests/test_workspace_api.py` (3 integration tests)
  - `frontend/src/client/generated/*` (regenerated)
  - `frontend/src/client/openapi/workspace.openapi.json` (regenerated)

### Phase 26: Semantic Embedding & FAISS Vector Search
- **Status:** complete
- Actions taken:
  - Created `backend/app/services/embedding.py` wrapping sentence-transformers (MiniLM-L12-v2, 384-dim) with lazy loading and zero-vector CI fallback.
  - Integrated FAISS `IndexFlatIP` per knowledge base: rebuild index after `add_knowledge_document()`, search via inner product on normalized vectors.
  - Replaced character-overlap `_chunk_score()`/`_search_chars()` with FAISS semantic search in `_retrieve_knowledge_citations()`.
  - Fixed `_compose_rag_answer()` — removed hardcoded microscope response, uses generic snippet composition.
  - Added `backend/tests/test_embedding.py` with 10 tests: shape, normalization, semantic similarity, cross-language, empty input, FAISS retrieval integration.
  - Added `pytest` and `httpx` to backend dev dependencies (Tsingshua mirror was down, switched to default PyPI).
  - Full verification: 66 backend tests, 62 frontend tests, type check, build all pass.
- Files created/modified:
  - `backend/app/services/embedding.py` (NEW)
  - `backend/tests/test_embedding.py` (NEW — 10 tests)
  - `backend/app/services/workspace.py` (FAISS index storage, `_rebuild_kb_faiss_index()`, `_find_document_and_chunk()`, rewired `_retrieve_knowledge_citations()`, fixed `_compose_rag_answer()`)
  - `backend/pyproject.toml` (added pytest, httpx dev deps)
  - `backend/tests/test_workspace_api.py` (updated QA assertion for non-hardcoded answer)

## Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Backend MVP API contracts | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python -m pytest tests/test_workspace_api.py -q` | Auth, file, RAG, agent, and workflow endpoint tests pass | `5 passed, 1 warning in 0.30s` | Pass |
| Frontend workspace unit test | `cd frontend && pnpm test:unit src/views/__tests__/WorkspaceView.spec.ts --run` | Workbench renders file, RAG, agent, workflow, team, and audit states | `1 passed` | Pass |
| Frontend architecture test | `cd frontend && pnpm test:unit tests/frontendArchitecture.spec.ts --run` | Agreed `src/` boundaries and desktop/mobile layout split are enforced | `1 passed, 3 tests passed` | Pass |
| Frontend generated client test | `cd frontend && pnpm test:unit tests/frontendArchitecture.spec.ts --run` | OpenAPI config/scripts exist and workspace live calls use generated SDK instead of axios | `1 passed, 5 tests passed` | Pass |
| Frontend all unit tests | `cd frontend && pnpm test:unit --run` | All Vitest tests pass | `2 passed, 4 tests passed` | Pass |
| Frontend type check | `cd frontend && pnpm type-check` | Vue/TypeScript project type-checks | exit 0 | Pass |
| Frontend production build | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass | build passed with a chunk-size warning for the Naive UI bundle | Pass |
| Browser visual/runtime check | DevTools at `http://127.0.0.1:5174/` | Desktop/mobile render without text overlap, horizontal overflow, or console errors | desktop `scrollWidth=1425`, `clientWidth=1425`; mobile `scrollWidth=390`, `clientWidth=390`; mobile DataTable hidden and 3 grouped rows rendered; no console errors/warnings/issues | Pass |
| Frontend architecture browser check | DevTools at `http://127.0.0.1:5174/` | Desktop uses desktop layout and phone uses mobile layout | desktop `hasDesktopAside=true`, `hasMobileHeader=false`; mobile `hasDesktopAside=false`, `hasMobileHeader=true`; no console errors/warnings/issues | Pass |
| OpenAPI client generation | `cd frontend && pnpm generate:client` | Backend exports schema and hey-api generates SDK/types under `src/client/generated/` | generated 4 hey-api output groups with `baseUrl: '/'` | Pass |
| Frontend auth focused tests | `cd frontend && pnpm test:unit --run src/stores/__tests__/auth.spec.ts src/views/__tests__/LoginView.spec.ts src/router/__tests__/authGuard.spec.ts` | Auth store, login view, and protected route guard pass | `3 passed, 6 tests passed` | Pass |
| Frontend all unit tests after auth | `cd frontend && pnpm test:unit --run` | All Vitest tests pass | `5 passed, 12 tests passed` | Pass |
| Frontend production build after auth | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass | build passed with the known Naive UI chunk-size warning | Pass |
| OpenAPI client regeneration after auth | `cd frontend && pnpm generate:client` | Backend export and hey-api generation still pass | generated 4 files under `src/client/generated` | Pass |
| Backend all current tests | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python -m pytest tests/test_workspace_api.py tests/test_openapi_export.py -q` | API contracts and OpenAPI export contracts pass | `6 passed, 1 warning` | Pass |
| Backend refresh-token slice | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python -m pytest tests/test_workspace_api.py tests/test_openapi_export.py -q` | API contracts, OpenAPI export, and refresh-token boundaries pass | `7 passed, 1 warning` | Pass |
| Frontend refresh-session slice | `cd frontend && pnpm test:unit --run` | Auth refresh action, router, login view, workspace, and architecture tests pass | `5 passed, 13 tests passed` | Pass |
| OpenAPI client regeneration after refresh | `cd frontend && pnpm generate:client` | Backend schema exports and hey-api regenerates refresh endpoint SDK/types | generated 4 files under `src/client/generated` | Pass |
| Frontend production build after refresh | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass | build passed with the known Naive UI chunk-size warning | Pass |
| Backend profile slice red test | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python -m pytest tests/test_workspace_api.py -q` | New profile tests fail before implementation | `2 failed, 6 passed`; `PATCH /api/v1/users/me` returned 405 | Expected Fail |
| Backend profile slice green test | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python -m pytest tests/test_workspace_api.py -q` | Current-user profile updates and duplicate email rejection pass | `8 passed, 1 warning` | Pass |
| Frontend profile slice red test | `cd frontend && pnpm test:unit --run src/stores/__tests__/auth.spec.ts src/router/__tests__/authGuard.spec.ts src/views/__tests__/ProfileView.spec.ts` | New frontend profile tests fail before implementation | missing `ProfileView.vue`, unmatched `/profile`, and `auth.updateProfile is not a function` | Expected Fail |
| Frontend profile focused tests | `cd frontend && pnpm test:unit --run src/stores/__tests__/auth.spec.ts src/router/__tests__/authGuard.spec.ts src/views/__tests__/ProfileView.spec.ts` | Store, route guard, and ProfileView profile update behavior pass | `3 passed, 9 tests passed` | Pass |
| Backend all current tests after profile | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python -m pytest tests/test_workspace_api.py tests/test_openapi_export.py -q` | API contracts and OpenAPI export contracts pass | `9 passed, 1 warning` | Pass |
| Frontend all unit tests after profile | `cd frontend && pnpm test:unit --run` | All Vitest tests pass | `6 passed, 16 tests passed` | Pass |
| OpenAPI client regeneration after profile | `cd frontend && pnpm generate:client` | Backend schema exports and hey-api regenerates profile update SDK/types | generated 4 files under `src/client/generated` | Pass |
| Frontend production build after profile | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass | build passed with the known Naive UI chunk-size warning | Pass |
| Frontend dev proxy red test | `cd frontend && pnpm test:unit --run tests/frontendArchitecture.spec.ts` | Local Vite proxy contract catches the missing/mismatched FastAPI target before config fix | `1 failed, 5 passed`; assertion expected `'/api'` and `target: 'http://127.0.0.1:8000'` | Expected Fail |
| Frontend dev proxy green test | `cd frontend && pnpm test:unit --run tests/frontendArchitecture.spec.ts` | Architecture contract passes after Vite proxy targets FastAPI on `127.0.0.1:8000` | `1 passed, 6 tests passed` | Pass |
| Frontend all unit tests after dev proxy | `cd frontend && pnpm test:unit --run` | All Vitest tests pass after proxy config change | `6 passed, 17 tests passed` | Pass |
| Backend all current tests after dev proxy | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python -m pytest` | API contracts and OpenAPI export contracts remain green | `9 passed, 1 warning` | Pass |
| OpenAPI client regeneration after dev proxy | `cd frontend && pnpm generate:client` | Backend schema export and hey-api generation still pass | generated 4 files under `src/client/generated` | Pass |
| Frontend production build after dev proxy | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass | build passed with the known chunk-size warning | Pass |
| Backend lockout red test | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python -m pytest tests/test_workspace_api.py -q` | New FR-U05 tests fail before implementation | `2 failed, 8 passed`; wrong-password responses lacked `failed_attempts` | Expected Fail |
| Backend lockout green test | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python -m pytest tests/test_workspace_api.py -q` | Failed login counting, 5-attempt lockout, success reset, and audit events pass | `10 passed, 1 warning` | Pass |
| OpenAPI login error red test | `cd backend && uv run --no-project --with fastapi --with pytest --with python-multipart -- python -m pytest tests/test_openapi_export.py -q` | Login OpenAPI contract exposes 401/423 `ErrorResponse` | failed with `KeyError: '401'` | Expected Fail |
| OpenAPI login error green test | same command | Login OpenAPI contract exposes 401/423 `ErrorResponse` | `1 passed` | Pass |
| Frontend lockout red test | `cd frontend && pnpm test:unit --run src/stores/__tests__/auth.spec.ts` | `ACCOUNT_LOCKED` maps to a clear lockout message | failed: expected lockout message, received generic invalid-credential message | Expected Fail |
| Frontend lockout green test | same command | Auth store maps generated `ErrorResponse` lockout detail to Chinese message | `1 passed, 6 tests passed` | Pass |
| Backend all current tests after lockout | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python -m pytest` | API contracts and OpenAPI export contracts pass | `11 passed, 1 warning` | Pass |
| Frontend all unit tests after lockout | `cd frontend && pnpm test:unit --run` | All Vitest tests pass | `6 passed, 18 tests passed` | Pass |
| OpenAPI client regeneration after lockout | `cd frontend && pnpm generate:client` | Backend schema exports and hey-api generates login 401/423 error types | generated 4 files under `src/client/generated` | Pass |
| Frontend production build after lockout | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass | build passed with the known chunk-size warning | Pass |
| Backend file lifecycle red test | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python -m pytest tests/test_workspace_api.py -q` | New file download/delete tests fail before implementation | `2 failed, 10 passed`; download and delete routes returned 404 | Expected Fail |
| Backend file lifecycle green test | same command | Download returns uploaded bytes, delete removes the file, repeat delete returns `FILE_NOT_FOUND`, audit events recorded | `12 passed, 1 warning` | Pass |
| Frontend file actions red test | `cd frontend && pnpm test:unit --run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/FileWorkbench.spec.ts` | Store and component tests fail before frontend implementation | missing `downloadWorkspaceFile`/`deleteWorkspaceFile` and missing row action buttons | Expected Fail |
| Frontend file actions focused tests | same command | Store calls generated-client adapter and FileWorkbench emits download/delete events | `2 passed, 3 tests passed` | Pass |
| Backend all current tests after file lifecycle | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python -m pytest` | API contracts and OpenAPI export contracts pass | `13 passed, 1 warning` | Pass |
| Frontend all unit tests after file lifecycle | `cd frontend && pnpm test:unit --run` | All Vitest tests pass | `8 passed, 21 tests passed` | Pass |
| OpenAPI client regeneration after file lifecycle | `cd frontend && pnpm generate:client` | Backend schema exports and hey-api regenerates download/delete SDK functions | generated 4 files under `src/client/generated` | Pass |
| Frontend production build after file lifecycle | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass | build passed with the known chunk-size warning | Pass |
| Frontend file search/upload red test | `cd frontend && pnpm test:unit --run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/FileWorkbench.spec.ts` | New file search/upload tests fail before implementation | `4 failed`; missing `listWorkspaceFiles`/`uploadWorkspaceFile`, missing search/upload controls | Expected Fail |
| Frontend file search/upload focused tests | same command | Store calls generated-client list/upload adapters and FileWorkbench emits search/upload events | `2 passed, 7 tests passed` | Pass |
| Frontend all unit tests after file search/upload | `cd frontend && pnpm test:unit --run` | All Vitest tests pass | `8 passed, 25 tests passed` | Pass |
| Frontend type check after file search/upload | `cd frontend && pnpm type-check` | Vue/TypeScript project type-checks | exit 0 | Pass |
| Frontend production build after file search/upload | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass | build passed with the known chunk-size warning | Pass |
| Phase 13 final frontend unit tests | `cd frontend && pnpm test:unit --run` | All frontend tests remain green after documentation cleanup | `8 passed, 25 tests passed` | Pass |
| Phase 13 final frontend type check | `cd frontend && pnpm type-check` | Vue/TypeScript project type-checks after documentation cleanup | exit 0 | Pass |
| Phase 13 final frontend production build | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass after documentation cleanup | build passed with the known Naive UI chunk-size warning | Pass |
| Phase 13 final backend tests | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest` | Backend API and OpenAPI contracts remain green | `13 passed, 1 warning` | Pass |
| Backend folder CRUD red test | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest tests/test_workspace_api.py tests/test_openapi_export.py -q` | New folder CRUD/API tests fail before implementation | `3 failed, 12 passed`; `/api/v1/folders` returned 404 and OpenAPI lacked folder path | Expected Fail |
| Backend folder CRUD green test | same command | Folder create/tree/move/delete validations and OpenAPI folder paths pass | `15 passed, 1 warning` | Pass |
| Frontend folder UI red test | `cd frontend && pnpm test:unit --run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/FolderTreePanel.spec.ts src/components/workspace/__tests__/FileWorkbench.spec.ts` | New folder store/component tests fail before implementation | missing `listWorkspaceFolders` and missing `FolderTreePanel.vue` | Expected Fail |
| Frontend folder focused tests | same command | Store folder adapters/actions and FolderTreePanel/FileWorkbench behavior pass | `3 passed, 15 tests passed` | Pass |
| Phase 14 frontend type check | `cd frontend && pnpm type-check` | Vue/TypeScript project type-checks after folder UI wiring | exit 0 | Pass |
| Phase 14 frontend unit tests | `cd frontend && pnpm test:unit --run` | All frontend tests remain green | `9 passed, 33 tests passed` | Pass |
| Phase 14 frontend production build | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass after folder UI wiring | build passed with the known Naive UI chunk-size warning | Pass |
| Phase 14 OpenAPI client generation | `cd frontend && pnpm generate:client` | `python3` backend export and hey-api generation pass | generated 4 files under `src/client/generated` | Pass |
| Phase 14 backend tests | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest` | Backend API and OpenAPI contracts remain green | `15 passed, 1 warning` | Pass |
| Backend file lifecycle update/copy/version red test | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest tests/test_workspace_api.py::test_file_update_copy_and_folder_validation_are_audited tests/test_workspace_api.py::test_same_name_upload_creates_versions_and_restore_creates_new_current_version tests/test_openapi_export.py::test_export_openapi_writes_workspace_contract -q` | New file lifecycle/API tests fail before implementation | `3 failed`; update/copy/version routes missing and same-name upload created a separate file | Expected Fail |
| Backend file lifecycle update/copy/version green test | same command | File rename/move/tag/copy/version/restore behavior and OpenAPI paths pass | `3 passed, 1 warning` | Pass |
| Phase 15 backend tests | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest -q` | Backend API and OpenAPI contracts remain green after lifecycle implementation | `17 passed, 1 warning` | Pass |
| Phase 15 OpenAPI client generation | `cd frontend && pnpm generate:client` | Backend schema export and hey-api generation expose lifecycle SDK/types | generated 4 files under `src/client/generated` | Pass |
| Frontend file lifecycle red test | `cd frontend && pnpm test:unit --run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/FileWorkbench.spec.ts` | New store/component lifecycle tests fail before implementation | `4 failed`; missing adapters/actions and lifecycle panel controls | Expected Fail |
| Frontend file lifecycle focused tests | same command | Store lifecycle actions and FileWorkbench lifecycle panel events pass | `2 passed, 15 tests passed` | Pass |
| Phase 15 frontend type check | `cd frontend && pnpm type-check` | Vue/TypeScript project type-checks after lifecycle UI wiring | exit 0 | Pass |
| Phase 15 frontend unit tests | `cd frontend && pnpm test:unit --run` | All frontend tests remain green | `9 passed, 37 tests passed` | Pass |
| Phase 15 frontend production build | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass after lifecycle UI wiring | build passed with the known Naive UI chunk-size warning | Pass |
| Phase 15 JSON validation | `python3 -m json.tool .wolf/buglog.json` | OpenWolf bug log remains valid JSON | exit 0 | Pass |
| Phase 15 whitespace check | `git diff --check` | No whitespace errors in the worktree diff | exit 0 | Pass |
| Backend team membership red test | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest tests/test_workspace_api.py::test_team_invites_role_updates_and_removal_are_audited tests/test_workspace_api.py::test_team_folder_permissions_enforce_guest_read_only_and_member_write tests/test_openapi_export.py::test_export_openapi_writes_workspace_contract -q` | New team/API tests fail before implementation | `3 failed`; team POST/routes and OpenAPI paths missing | Expected Fail |
| Backend team membership green test | same command | Team create/invite/member update/remove, audit events, and team-folder permission checks pass | `3 passed, 1 warning` | Pass |
| Phase 16 OpenAPI client generation | `cd frontend && pnpm generate:client` | Backend schema export and hey-api generation expose team SDK/types | generated 4 files under `src/client/generated` | Pass |
| Frontend team membership red test | `cd frontend && pnpm test:unit --run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/TeamAuditPanel.spec.ts` | New store/component team tests fail before implementation | `3 failed`; missing team-summary helper and panel controls | Expected Fail |
| Frontend team membership focused tests | same command | Store team actions and TeamAuditPanel create/invite/member events pass | `2 passed, 14 tests passed` | Pass |
| Phase 16 frontend unit tests | `cd frontend && pnpm test:unit --run` | All frontend tests remain green after team UI wiring | `10 passed, 40 tests passed` | Pass |
| Phase 16 frontend type check | `cd frontend && pnpm type-check` | Vue/TypeScript project type-checks after team UI wiring | exit 0 | Pass |
| Phase 16 frontend production build | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass after team UI wiring | build passed with the known Naive UI chunk-size warning | Pass |
| Phase 16 backend tests | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest -q` | Backend API and OpenAPI contracts remain green after team implementation | `19 passed, 1 warning` | Pass |
| Phase 16 JSON validation | `python3 -m json.tool .wolf/buglog.json` | OpenWolf bug log remains valid JSON | exit 0 | Pass |
| Phase 16 whitespace check | `git diff --check` | No whitespace errors in the worktree diff | exit 0 | Pass |
| Backend knowledge-base/RAG focused tests | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest tests/test_workspace_api.py::test_knowledge_base_create_update_document_index_and_qa_are_audited tests/test_workspace_api.py::test_qa_query_returns_answer_with_citations tests/test_openapi_export.py::test_export_openapi_writes_workspace_contract -q` | Knowledge-base CRUD, document indexing, cited QA, and OpenAPI paths pass | `3 passed, 1 warning` | Pass |
| Frontend RAG view wiring red test | `cd frontend && pnpm test:unit --run src/views/__tests__/WorkspaceView.spec.ts` | New WorkspaceView wiring test fails before the view passes RAG props/events | failed on missing `[data-testid="select-kb-kb-biology"]` | Expected Fail |
| Frontend RAG focused tests | `cd frontend && pnpm test:unit --run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/RagInsightPanel.spec.ts src/views/__tests__/WorkspaceView.spec.ts` | Store adapters/actions, RagInsightPanel interactions, and WorkspaceView wiring pass | `3 passed, 17 tests passed` | Pass |
| Phase 17 frontend type check | `cd frontend && pnpm type-check` | Vue/TypeScript project type-checks after RAG UI wiring | exit 0 | Pass |
| Phase 17 frontend unit tests | `cd frontend && pnpm test:unit --run` | All frontend tests remain green after RAG UI wiring | `11 passed, 44 tests passed` | Pass |
| Phase 17 frontend production build | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass after RAG UI wiring | build passed with the known Naive UI chunk-size warning | Pass |
| Phase 17 backend tests | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest -q` | Backend API and OpenAPI contracts remain green after knowledge-base/RAG implementation | `20 passed, 1 warning` | Pass |
| Phase 17 OpenAPI client generation | `cd frontend && pnpm generate:client` | Backend schema export and hey-api generation expose knowledge-base SDK/types | generated 4 files under `src/client/generated` | Pass |
| Backend workflow definition red test | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest tests/test_workspace_api.py::test_workflow_definition_create_update_validate_publish_execute_and_audit tests/test_workspace_api.py::test_workflow_validation_rejects_cycles_and_invalid_tool_nodes_before_publish tests/test_openapi_export.py::test_export_openapi_writes_workspace_contract -q` | New workflow/API tests fail before implementation | `POST /api/v1/workflows` returned 405 and OpenAPI lacked `POST /api/v1/workflows` | Expected Fail |
| Backend workflow definition focused tests | same command | Workflow create/update/validate/publish/execute behavior and OpenAPI paths pass | `3 passed, 1 warning` | Pass |
| Phase 18 OpenAPI client generation | `cd frontend && pnpm generate:client` | Backend schema export and hey-api generation expose workflow SDK/types | generated workflow create/update/validate/publish/execute functions under `src/client/generated` | Pass |
| Frontend workflow builder red test | `cd frontend && pnpm test:unit --run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/AgentWorkflowPanel.spec.ts src/views/__tests__/WorkspaceView.spec.ts` | New workflow store/component/view tests fail before implementation | missing workflow adapters/actions, old read-only panel, and missing view workflow wiring | Expected Fail |
| Frontend workflow focused tests | same command | Store workflow actions, AgentWorkflowPanel interactions, and WorkspaceView wiring pass | `3 passed, 19 tests passed` | Pass |
| Phase 18 frontend type check | `cd frontend && pnpm type-check` | Vue/TypeScript project type-checks after workflow UI wiring | exit 0 | Pass |
| Phase 18 frontend unit tests | `cd frontend && pnpm test:unit --run` | All frontend tests remain green after workflow UI wiring | `12 passed, 48 tests passed` | Pass |
| Phase 18 frontend production build | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass after workflow UI wiring | build passed with the known large-chunk warning | Pass |
| Phase 18 backend tests | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest -q` | Backend API and OpenAPI contracts remain green after workflow implementation | `22 passed, 1 warning` | Pass |
| Phase 18 JSON validation | `python3 -m json.tool .wolf/buglog.json` | OpenWolf bug log remains valid JSON | exit 0 | Pass |
| Phase 18 whitespace check | `git diff --check` | No whitespace errors in the worktree diff | exit 0 | Pass |
| Phase 19 RBAC red test | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest tests/test_workspace_api.py::test_team_file_read_and_write_permissions_are_enforced_across_resources -q` | New cross-resource RBAC test fails before implementation | failed because outsider file search returned the team file | Expected Fail |
| Phase 19 RBAC focused test | same command | Outsider cannot list/download/index/execute team file; guest can read but cannot update/delete | `1 passed, 1 warning` | Pass |
| Phase 19 backend tests | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest -q` | Backend API and OpenAPI contracts remain green after RBAC enforcement | `23 passed, 1 warning` | Pass |
| Phase 19 OpenAPI client generation | `cd frontend && pnpm generate:client` | Backend schema export and hey-api generation still pass after RBAC-only route signature changes | generated 4 files under `src/client/generated` | Pass |
| Phase 19 frontend type check | `cd frontend && pnpm type-check` | Vue/TypeScript project type-checks after client regeneration | exit 0 | Pass |
| Phase 19 frontend unit tests | `cd frontend && pnpm test:unit --run` | All frontend tests remain green after RBAC client regeneration | `12 passed, 48 tests passed` | Pass |
| Phase 19 frontend production build | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass after RBAC client regeneration | build passed with the known large-chunk warning | Pass |
| Phase 19 JSON validation | `python3 -m json.tool .wolf/buglog.json` | OpenWolf bug log remains valid JSON | exit 0 | Pass |
| Phase 19 whitespace check | `git diff --check` | No whitespace errors in the worktree diff | exit 0 | Pass |
| Phase 19 services-boundary check | `rg --files frontend/src \| rg '(^|/)services/'` | Frontend `services/` directory remains deleted | no output, exit 1 | Pass |
| Backend permission rules focused test | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest tests/test_workspace_api.py::test_permission_rules_support_inheritance_overrides_and_audit_events tests/test_openapi_export.py::test_export_openapi_writes_workspace_contract -q` | Permission rules list/create/delete, deny precedence, inheritance/override checks, audit events, and OpenAPI paths pass | focused tests passed with the known Starlette warning | Pass |
| Phase 20 OpenAPI client generation | `cd frontend && pnpm generate:client` | Backend schema export and hey-api generation expose permission rule SDK/types | generated `permissionRulesApiV1PermissionsRulesGet`, `createPermissionRuleApiV1PermissionsRulesPost`, and `deletePermissionRuleApiV1PermissionsRulesRuleIdDelete` | Pass |
| Frontend permission rules red test | `cd frontend && pnpm test:unit --run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/PermissionRulesPanel.spec.ts src/views/__tests__/WorkspaceView.spec.ts` | New store/component/view permission tests fail before implementation | failed on missing permission adapters/actions/panel wiring | Expected Fail |
| Frontend permission rules focused tests | same command | Store permission actions, PermissionRulesPanel interactions, and WorkspaceView wiring pass | `3 passed, 20 tests passed` | Pass |
| Phase 20 frontend type check | `cd frontend && pnpm type-check` | Vue/TypeScript project type-checks after permission panel wiring | exit 0 | Pass |
| Phase 20 frontend unit tests | `cd frontend && pnpm test:unit --run` | All frontend tests remain green after permission panel wiring | `13 passed, 51 tests passed` | Pass |
| Phase 20 frontend production build | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass after permission panel wiring | build passed with the known large-chunk warning | Pass |
| Phase 20 backend tests | `cd backend && uv run --no-project --with fastapi --with httpx --with pytest --with python-multipart -- python3 -m pytest -q` | Backend API and OpenAPI contracts remain green after ACL rules | `24 passed, 1 warning` | Pass |
| Phase 20 JSON validation | `python3 -m json.tool .wolf/buglog.json` | OpenWolf bug log remains valid JSON | exit 0 | Pass |
| Phase 20 whitespace check | `git diff --check` | No whitespace errors in the worktree diff | exit 0 | Pass |
| Phase 20 services-boundary check | `rg --files frontend/src \| rg '(^|/)services/'` | Frontend `services/` directory remains deleted | no output, exit 1 | Pass |
| Phase 22 FR-F07 backend red test | `cd backend && PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "updated_time_range"` | New updated-time range test fails before implementation because `/api/v1/files` ignores `updated_from`/`updated_to` | failed with both tagged uploads returned | Expected Fail |
| Phase 22 FR-F07 frontend red tests | `cd frontend && pnpm vitest run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/FileWorkbench.spec.ts -t "search"` | Store drops updated-time filter fields and FileWorkbench has no updated-time inputs before implementation | 2 expected failures | Expected Fail |
| Phase 22 backend focused test | `cd backend && PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "updated_time_range"` | File listing filters by inclusive `updated_from`/`updated_to` bounds | `1 passed, 27 deselected, 1 warning` | Pass |
| Phase 22 frontend focused tests | `cd frontend && pnpm vitest run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/FileWorkbench.spec.ts -t "search"` | Store forwards updated-time filters and FileWorkbench emits toolbar bounds | `2 files passed, 2 tests passed` | Pass |
| Phase 22 OpenAPI client generation | `cd frontend && pnpm generate:client` | Generated OpenAPI schema/types expose `updated_from` and `updated_to` on `GET /api/v1/files` | generated 4 files under `src/client/generated` | Pass |
| Phase 22 backend tests | `cd backend && PYTHONPATH=. uv run python -m pytest -q` | Backend API contracts remain green after updated-time filtering | `29 passed, 1 warning` | Pass |
| Phase 22 frontend unit tests | `cd frontend && pnpm vitest run` | Frontend tests remain green after filter UI/store changes | `13 files passed, 54 tests passed` | Pass |
| Phase 22 frontend type check | `cd frontend && pnpm type-check` | Vue/TypeScript project type-checks after filter type expansion | exit 0 | Pass |
| Phase 22 frontend production build | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass after filter UI changes | build passed | Pass |
| Phase 22 JSON validation | `python3 -m json.tool .wolf/buglog.json >/dev/null` | OpenWolf bug log remains valid JSON | exit 0 | Pass |
| Phase 22 whitespace check | `git diff --check` | No whitespace errors in the worktree diff | exit 0 | Pass |
| Phase 23 annotations backend red test | `cd backend && PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k annotation` | New annotation test fails before implementation because `/api/v1/files/{file_id}/annotations` is missing | failed with 404 on annotation create | Expected Fail |
| Phase 23 annotations OpenAPI red test | `cd backend && PYTHONPATH=. uv run python -m pytest tests/test_openapi_export.py -q` | OpenAPI contract lacks annotation paths before implementation | failed missing `/api/v1/files/{file_id}/annotations` | Expected Fail |
| Phase 23 annotations frontend red tests | `cd frontend && pnpm vitest run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/FileAnnotationPanel.spec.ts -t annotation` | Store adapter functions and `FileAnnotationPanel.vue` are missing before implementation | failed on missing `listWorkspaceFileAnnotations` and missing panel import | Expected Fail |
| Phase 23 OpenAPI client generation | `cd frontend && pnpm generate:client` | Backend schema export and hey-api generation expose file annotation SDK/types | generated `fileAnnotations...`, `createFileAnnotation...`, `replyFileAnnotation...`, and `deleteFileAnnotation...` | Pass |
| Phase 23 backend focused tests | `cd backend && PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k annotation && PYTHONPATH=. uv run python -m pytest tests/test_openapi_export.py -q` | Annotation list/create/reply/delete, outsider denial, unread-count increment, audit events, and OpenAPI paths pass | 2 focused commands passed with known Starlette warning on API test | Pass |
| Phase 23 frontend focused tests | `cd frontend && pnpm vitest run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/FileAnnotationPanel.spec.ts -t annotation` | Store annotation actions and FileAnnotationPanel interactions pass | 2 files passed, 2 tests passed | Pass |
| Phase 23 workbench annotation tests | `cd frontend && pnpm vitest run src/components/workspace/__tests__/FileWorkbench.spec.ts src/components/workspace/__tests__/FileAnnotationPanel.spec.ts` | FileWorkbench opens annotation panel and forwards create events; panel render/create/reply/delete remains green | 2 files passed, 6 tests passed | Pass |
| Phase 23 backend tests | `cd backend && PYTHONPATH=. uv run python -m pytest -q` | Backend API contracts remain green after annotations | 30 passed, 1 warning | Pass |
| Phase 23 frontend unit tests | `cd frontend && pnpm vitest run` | Frontend tests remain green after annotation panel/store/view wiring | 14 files passed, 57 tests passed | Pass |
| Phase 23 frontend type check | `cd frontend && pnpm type-check` | Vue/TypeScript project type-checks after annotation wiring | exit 0 | Pass |
| Phase 23 frontend production build | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass after annotation wiring | build passed | Pass |
| Phase 23 JSON validation | `python3 -m json.tool .wolf/buglog.json >/dev/null` | OpenWolf bug log remains valid JSON | exit 0 | Pass |
| Phase 23 whitespace check | `git diff --check` | No whitespace errors in the worktree diff | exit 0 | Pass |
| Phase 24 backend focused notification tests | `cd backend && PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py::test_notifications_list_and_mark_read_for_invites_mentions_and_annotation_replies tests/test_workspace_api.py::test_team_file_annotations_support_replies_permissions_and_notifications tests/test_openapi_export.py -q` | Notification list/read behavior, invite/mention/reply signals, annotation notification compatibility, and OpenAPI paths pass | 3 passed, 1 warning | Pass |
| Phase 24 OpenAPI client generation | `cd frontend && pnpm generate:client` | Backend schema export and hey-api generation expose notification SDK/types | generated notification list/read contracts under `src/client/generated` | Pass |
| Phase 24 frontend focused notification tests | `cd frontend && pnpm vitest run src/stores/__tests__/workspace.spec.ts src/components/workspace/__tests__/NotificationInboxPanel.spec.ts src/components/workspace/__tests__/TeamAuditPanel.spec.ts -t notification` | Store notification actions, inbox panel render/read emits, and TeamAuditPanel forwarding pass | 3 files passed, 3 tests passed | Pass |
| Phase 24 backend tests | `cd backend && PYTHONPATH=. uv run python -m pytest -q` | Backend API contracts remain green after notification inbox | 31 passed, 1 warning | Pass |
| Phase 24 frontend unit tests | `cd frontend && pnpm vitest run` | Frontend tests remain green after notification panel/store/view wiring | 15 files passed, 60 tests passed | Pass |
| Phase 24 frontend type check | `cd frontend && pnpm type-check` | Vue/TypeScript project type-checks after notification wiring | exit 0 | Pass |
| Phase 24 frontend production build | `cd frontend && pnpm build` | `vue-tsc --build` and `vite build` pass after notification wiring | build passed | Pass |
| Phase 24 JSON validation | `python3 -m json.tool .wolf/buglog.json >/dev/null` | OpenWolf bug log remains valid JSON | exit 0 | Pass |
| Phase 24 whitespace check | `git diff --check` | No whitespace errors in the worktree diff | exit 0 | Pass |

## Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| 2026-07-11 00:00 | RAG/agent-flow refactor plan needed to be persisted locally before implementation | 1 | Created `docs/superpowers/plans/2026-07-11-rag-agent-flow-refactor.md` with staged backend/frontend/test tasks. |
| 2026-07-08 08:26 | `SyntaxError: bytes can only contain ASCII literal characters` in backend test upload payload | 1 | Encoded the Chinese Markdown fixture from `str` with `.encode()`. |
| 2026-07-08 08:36 | `uv pip install` waited on `backend/.venv/.lock` held by an existing `uv sync` process | 1 | Switched to running tests from `backend/` with `uv run --no-project --with ...` so the active sync is not interrupted. |
| 2026-07-08 08:36 | `ModuleNotFoundError: No module named 'app'` | 1 | Expected TDD red state before adding the backend application package. |
| 2026-07-08 08:37 | `ImportError: email-validator is not installed` from Pydantic `EmailStr` | 1 | Replaced `EmailStr` with a simple `str` field pattern so the declared backend dependencies are sufficient. |
| 2026-07-08 09:02 | `@pinia/testing` required `createSpy` | 1 | Passed `createSpy: vi.fn` in the workspace view test. |
| 2026-07-08 09:03 | Workspace test rendered unresolved Naive UI components | 1 | Mounted a Naive UI test host with `NConfigProvider` and the Naive plugin. |
| 2026-07-08 09:08 | RAG text overlapped in browser screenshot | 1 | Replaced ambiguous UnoCSS line-height utilities with arbitrary values. |
| 2026-07-08 09:10 | Mobile viewport had horizontal overflow | 1 | Added `scroll-x` to `NDataTable` and constrained workspace cards. |
| 2026-07-08 09:14 | `pnpm build` failed on stale starter imports | 1 | Removed unused starter test/views after starter components had been removed. |
| 2026-07-08 09:34 | Edge DevTools `resize_page` failed with `Browser.setContentsSize` while the window was not normal | 1 | Switched to viewport emulation for desktop and phone checks. |
| 2026-07-08 09:46 | `rmdir frontend/src/__tests__` failed from `frontend/` because the path included a duplicated `frontend/` prefix | 1 | Re-ran cleanup with the correct `src/__tests__` path. |
| 2026-07-08 09:56 | Importing `@vueuse/core` for `useMediaQuery` added Vite/Rolldown `INVALID_ANNOTATION` warnings | 1 | Replaced the dependency import with a small local Vue media-query composable. |
| 2026-07-08 10:10 | `ModuleNotFoundError: No module named 'app.openapi_export'` in OpenAPI export test | 1 | Added `backend/app/openapi_export.py` with an export helper and CLI entry point. |
| 2026-07-08 10:12 | Generated hey-api client used `baseUrl: 'src'` | 1 | Declared FastAPI OpenAPI `servers=[{"url": "/"}]` and regenerated the client. |
| 2026-07-08 10:14 | Frontend architecture test showed `workspace.ts` still imported axios directly | 1 | Rewired live snapshot calls through `workspaceSnapshotApiV1WorkspaceSnapshotGet` from `src/client/generated`. |
| 2026-07-08 10:34 | Login view test warned `Failed to resolve component: NSegmented` and could not find `注册账号` | 1 | Replaced unavailable `NSegmented` with Naive UI `NRadioGroup` and `NRadioButton`; focused tests passed. |
| 2026-07-08 10:44 | Backend refresh-token contract initially returned 404 for `/api/v1/auth/refresh` | 1 | Added refresh schema, route, service method, token-kind validation, and random `jti`; backend tests passed. |
| 2026-07-08 10:48 | Frontend auth test failed because `auth.refreshSession` did not exist | 1 | Added generated-client-backed `refreshSession()` action and persisted rotated tokens; frontend tests passed. |
| 2026-07-08 11:04 | Backend profile update tests received 405 for `PATCH /api/v1/users/me` | 1 | Added profile update schema, route, service method, duplicate email guard, and audit logging. |
| 2026-07-08 11:07 | Frontend profile tests failed because the route, view, and auth action were missing | 1 | Added `updateProfile()`, `/profile`, `ProfileView.vue`, and layout profile links. |
| 2026-07-08 13:59 | Frontend architecture test failed because Vite proxy config targeted `localhost:8000` and used a string form that did not match the local API proxy contract | 1 | Updated `frontend/vite.config.ts` so `/api` proxies to `http://127.0.0.1:8000`. |
| 2026-07-08 14:10 | Backend lockout tests failed because invalid-credential responses lacked failed-attempt details | 1 | Added login security state, account lockout, reset on success, and audit events. |
| 2026-07-08 14:12 | OpenAPI export test failed because login 401/423 responses were not documented | 1 | Added route response metadata with `ErrorResponse`. |
| 2026-07-08 14:11 | Frontend auth store lockout test failed because all login errors used the generic invalid-credential message | 1 | Added generated error narrowing and lockout message mapping. |
| 2026-07-08 14:23 | File download/delete backend tests returned 404 | 1 | Added in-memory file content storage, download/delete routes, and file audit events. |
| 2026-07-08 14:24 | Frontend file-action tests failed because generated-client adapters and row buttons were missing | 1 | Added generated SDK adapter functions, workspace store actions, and FileWorkbench download/delete controls. |
| 2026-07-08 14:27 | `pnpm build` failed with `string | undefined` token type errors in workspace store | 1 | Split optional and required access-token helpers so file actions receive a statically non-null token. |
| 2026-07-08 14:31 | File search/upload component failed to compile because a `defineProps` default referenced `emptyFilters` | 1 | Inlined the default filters object in the `withDefaults()` macro because Vue hoists `defineProps`. |
| 2026-07-08 14:32 | Type check rejected `demoWorkspaceSnapshot.files[0]` in workspace tests | 1 | Added a fixture helper that finds the demo file by id and throws if it is absent, preserving `FileItem` typing. |
| 2026-07-08 15:02 | Folder CRUD backend tests returned 404 and OpenAPI lacked folder routes | 1 | Added folder schemas, routes, service tree mutations, validation errors, audit events, and OpenAPI assertions. |
| 2026-07-08 15:07 | Frontend folder tests failed because adapter functions and `FolderTreePanel.vue` were missing | 1 | Added generated-client folder adapters, Pinia folder actions, folder tree panel, dynamic upload folder options, and view wiring. |
| 2026-07-08 15:35 | File lifecycle backend tests failed because update/copy/version routes and same-name upload versioning were missing | 1 | Added file lifecycle schemas, routes, service methods, version cache, folder validation, and audit events. |
| 2026-07-08 15:54 | FileWorkbench lifecycle test failed because no `manage-file-*` entry or lifecycle panel was wired | 1 | Added `FileLifecyclePanel.vue`, manage buttons in desktop/mobile rows, typed lifecycle emits, and `WorkspaceView` store handlers. |
| 2026-07-08 16:19 | Frontend team store test hit `ReferenceError: upsertTeamSummary is not defined` | 1 | Added immutable team-summary/detail merge helpers for the `shallowRef` workspace store state. |
| 2026-07-08 16:19 | TeamAuditPanel tests could not find team creation or invite/member controls | 1 | Replaced the read-only team panel with typed Naive UI forms, role actions, and event emits. |
| 2026-07-08 22:35 | Workflow panel type check rejected generated `position` maps for Vue Flow nodes | 1 | Normalized node positions to explicit `XYPosition` objects with `x` and `y`. |
| 2026-07-08 22:35 | AgentWorkflowPanel test emitted payload was typed as `unknown` and `wrapper.get().exists()` was invalid | 1 | Added a typed emitted-payload guard and switched the existence assertion to `find().exists()`. |
| 2026-07-08 22:48 | Phase 19 backend suite failed because workflow execution used seed team file `file-weekly` without team membership | 1 | Updated the workflow test to create a team, upload a team file as the owner, and execute the workflow against that accessible file. |
| 2026-07-09 12:08 | Frontend permission-rule tests failed because adapters, Pinia actions, and panel wiring were missing | 1 | Added generated-client permission adapters, store state/actions, `PermissionRulesPanel.vue`, and FileWorkbench/WorkspaceView event wiring. |
| 2026-07-09 12:08 | `PermissionRulesPanel.vue` type check rejected `subjectOptions.value[0]` / `resourceOptions.value[0]` as possibly undefined | 1 | Stored the first option in a local constant and guarded it before assigning `.value`. |

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | Phase 26 complete — semantic embeddings (sentence-transformers) and FAISS vector search integrated; 66 backend tests, keyword scoring replaced with cosine similarity |
| Where am I going? | Async parse queue (ARQ/Celery), OCR, persistent storage (MySQL/MinIO/FAISS persistence), drag/drop workflow editing, WebSocket delivery, live LLM API integration |
| What's the goal? | Build the report-aligned intelligent file management and agent collaboration platform |
| What have I learned? | See `findings.md` |
| What have I done? | Phases 1-26 complete: backend API (66 tests), Vue/Naive UI workbench MVP, OpenAPI generation, auth/refresh/profile/lockout, file CRUD/lifecycle/version/upload/search/download/delete/share/recycle, folder tree, team/RBAC, real parser (6 formats), semantic FAISS RAG, editable workflows, ACL rules, annotations/replies, notification inbox, and remote contributions (WorkflowBuilderView, TeamChatView, RagQaView, PermissionAuditView, guest login, demo user) |

## 2026-07-11 RAG/Agent Refactor Slice
| Time | Change | Files | Verification |
|------|--------|-------|--------------|
| 02:24 | Implemented the first backend slice for scoped knowledge-base metadata, soft delete, batch add/remove file membership, reindex/list-file endpoints, OpenAPI assertions, SQLite schema backfill, and v2 test auth isolation. | `backend/app/domain/knowledge.py`, `backend/app/models/knowledge.py`, `backend/app/services/workspace_db.py`, `backend/app/api/v2/knowledge.py`, `backend/tests/test_workspace_api.py`, `backend/tests/test_openapi_export.py`, `backend/alembic/versions/20260711_rag_agent_refactor.py` | `PYTHONPATH=. uv run python -m pytest -q` from `backend/` -> 85 passed, 3 warnings. |
| 02:37 | Added v2 RAG conversation persistence: knowledge conversation/message/citation snapshot tables, conversation list/detail APIs, persisted assistant `message_id`, OpenAPI path coverage, multi-turn retrieval history storage, and deterministic previous-question handling when the LLM ignores provided history. | `backend/app/domain/knowledge.py`, `backend/app/models/knowledge.py`, `backend/app/repositories/knowledge.py`, `backend/app/services/workspace_db.py`, `backend/app/services/llm.py`, `backend/app/api/v2/knowledge.py`, `backend/tests/test_workspace_api.py`, `backend/tests/test_openapi_export.py`, `backend/tests/test_llm.py`, `backend/alembic/versions/20260711_rag_agent_refactor.py` | Focused RAG/OpenAPI/embedding/LLM checks passed; backend full suite -> 87 passed, 3 warnings. |
| 02:59 | Added backend tool-flow executor slice: required tool catalog (`calculator`, `course_lookup`, `file_content_search`, `python_data`), explicit agent phases, structured inputs/outputs, result views, missing-parameter clarification, task detail, and continue routes. | `backend/app/domain/workflow.py`, `backend/app/services/tool_registry.py`, `backend/app/services/agent_executor.py`, `backend/app/services/workspace_db.py`, `backend/app/api/v2/knowledge.py`, `backend/tests/test_workspace_api.py`, `backend/tests/test_openapi_export.py` | `PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "agent or tools"` -> 11 passed; backend full suite -> 91 passed, 3 warnings. |
| 03:14 | Completed frontend OpenAPI/client adapter slice and started RAG store refactor: regenerated client, added KB delete/batch/reindex/conversation/tool/agent detail/continue adapters, expanded `knowledge.ts` for scoped metadata, batch membership, conversations, and reindex state. | `frontend/src/client/workspace.ts`, `frontend/src/stores/knowledge.ts`, `frontend/src/stores/__tests__/knowledge.spec.ts`, `frontend/src/components/workflow/AgentWorkflowPanel.vue`, `frontend/src/stores/workspace.ts`, `frontend/src/views/__tests__/TeamChatView.spec.ts`, `frontend/src/client/generated/*`, `frontend/src/client/openapi/workspace.openapi.json` | `pnpm type-check` -> pass; `pnpm vitest run src/stores/__tests__/knowledge.spec.ts` -> 4 passed; `pnpm vitest run src/stores/__tests__/workspace.spec.ts` -> 25 passed. |
| 03:29 | Completed Task 7 RAG frontend slice: added knowledge-base sidebar/manager, file picker, conversation panel, citation list, expanded store tests for team scope/update/delete/multi-turn question context, and refactored `RagQaView.vue` to use `useKnowledgeStore`. | `frontend/src/views/RagQaView.vue`, `frontend/src/components/rag/KnowledgeBaseSidebar.vue`, `frontend/src/components/rag/KnowledgeBaseManager.vue`, `frontend/src/components/rag/KnowledgeFilePicker.vue`, `frontend/src/components/rag/KnowledgeConversationPanel.vue`, `frontend/src/components/rag/KnowledgeCitationList.vue`, `frontend/src/components/rag/__tests__/KnowledgeFilePicker.spec.ts`, `frontend/src/components/rag/__tests__/KnowledgeConversationPanel.spec.ts`, `frontend/src/stores/knowledge.ts`, `frontend/src/stores/__tests__/knowledge.spec.ts` | `pnpm vitest run src/stores/__tests__/knowledge.spec.ts src/components/rag/__tests__/KnowledgeFilePicker.spec.ts src/components/rag/__tests__/KnowledgeConversationPanel.spec.ts` -> 13 passed; `pnpm type-check` -> pass. |
| 03:35 | Completed Task 8 agent/tool-flow frontend slice: added `agent.ts` store, tool catalog/task composer/execution timeline/result viewer components, and refactored `WorkflowBuilderView.vue` to use agent store actions instead of direct debug `fetch()` calls. | `frontend/src/stores/agent.ts`, `frontend/src/stores/__tests__/agent.spec.ts`, `frontend/src/components/workflow/AgentTaskComposer.vue`, `frontend/src/components/workflow/ToolCatalogPanel.vue`, `frontend/src/components/workflow/AgentExecutionTimeline.vue`, `frontend/src/components/workflow/ToolResultViewer.vue`, `frontend/src/components/workflow/__tests__/AgentExecutionTimeline.spec.ts`, `frontend/src/views/WorkflowBuilderView.vue`, `frontend/src/client/workspace.ts` | `pnpm vitest run src/stores/__tests__/agent.spec.ts src/components/workflow/__tests__/AgentExecutionTimeline.spec.ts` -> 4 passed; `pnpm type-check` -> pass; `rg "fetch\\(" frontend/src/views/WorkflowBuilderView.vue` -> no matches. |
| 03:38 | Ran Task 9 full integration verification and updated planning files. Transitional workspace-store RAG/agent compatibility remains because `WorkspaceView` still consumes it, while `/rag` and `/workflow` now use standalone stores/components. | `docs/superpowers/plans/2026-07-11-rag-agent-flow-refactor.md`, `task_plan.md`, `findings.md`, `progress.md` | Backend full suite -> 91 passed, 3 warnings; frontend full unit suite -> 14 files/67 tests passed; `pnpm type-check` -> pass; `pnpm build` -> pass; buglog JSON and `git diff --check` -> pass. |
| 03:46 | Completed remaining Task 4 backend cleanup: extracted `RagPipeline`, added explicit QA `error_code` handling for empty KB, unindexed files, and no-match states, regenerated the frontend client, and re-ran final verification. | `backend/app/services/rag_pipeline.py`, `backend/app/services/workspace_db.py`, `backend/app/domain/knowledge.py`, `backend/tests/test_workspace_api.py`, `frontend/src/client/generated/*`, `frontend/src/client/openapi/workspace.openapi.json`, `docs/superpowers/plans/2026-07-11-rag-agent-flow-refactor.md` | Focused RAG tests -> 7 passed; embedding/LLM tests -> 16 passed; backend full suite -> 92 passed, 3 warnings; frontend full unit suite -> 14 files/67 tests passed; `pnpm type-check`, `pnpm build`, JSON validation, and `git diff --check` passed. |
| 03:58 | Refined RAG knowledge Q&A page interaction: softened the left knowledge-base selector styling, moved file management and conversations into tabs, added new-conversation flow, old-conversation view/continue, and real conversation deletion. | `backend/app/api/v2/knowledge.py`, `backend/app/repositories/knowledge.py`, `backend/app/services/workspace_db.py`, `backend/tests/test_workspace_api.py`, `backend/tests/test_openapi_export.py`, `frontend/src/client/workspace.ts`, `frontend/src/stores/knowledge.ts`, `frontend/src/components/rag/KnowledgeBaseSidebar.vue`, `frontend/src/components/rag/KnowledgeConversationPanel.vue`, `frontend/src/views/RagQaView.vue`, `frontend/src/components/rag/__tests__/KnowledgeConversationPanel.spec.ts`, `frontend/src/stores/__tests__/knowledge.spec.ts`, `frontend/src/client/generated/*`, `frontend/src/client/openapi/workspace.openapi.json` | Focused backend/OpenAPI tests passed; focused frontend RAG/store tests -> 15 passed; backend full suite -> 92 passed, 3 warnings; frontend full unit suite -> 14 files/69 tests passed; `pnpm type-check`, `pnpm build`, JSON validation, and `git diff --check` passed. |
| 04:11 | Fixed RAG file scope isolation: team knowledge bases reject personal files and only show matching team-space files in the frontend picker; personal knowledge bases hide team files. | `backend/app/services/workspace_db.py`, `backend/tests/test_workspace_api.py`, `frontend/src/stores/knowledge.ts`, `frontend/src/stores/__tests__/knowledge.spec.ts`, `backend/tests/test_embedding.py` | Focused backend scope tests -> 2 passed; focused frontend knowledge tests -> 12 passed; backend full suite -> 93 passed, 3 warnings; frontend full unit suite -> 14 files/70 tests passed; `pnpm type-check`, `pnpm build`, JSON validation, and `git diff --check` passed. |
| 04:47 | Planned personal-folder and complete tool-flow implementation: saved a detailed plan, added Phase 29-31 to the root task plan, and recorded key gaps in current code. | `docs/superpowers/plans/2026-07-11-folder-agent-flow-completion.md`, `task_plan.md` | Planning only; identified unresolved upload folder ids, placeholder multipart completion, process-memory agent tasks, single-tool routing, and inline `course_lookup` data as implementation targets. |
| 05:02 | Implemented personal-folder hardening and v2 tool-flow completion slice: per-user personal root is created on tree load, legacy upload folder ids normalize to the current user root, multipart upload now tracks chunks and completes through real file upload, agent tasks/steps persist in DB, multi-tool planning runs ordered tools, course lookup reads `backend/app/data/courses.json`, and result UI renders mixed/chart outputs. | `backend/app/services/workspace_db.py`, `backend/app/services/agent_executor.py`, `backend/app/services/tool_registry.py`, `backend/app/models/workflow.py`, `backend/app/repositories/workflow.py`, `backend/tests/test_workspace_api.py`, `frontend/src/components/workflow/ToolResultViewer.vue`, `frontend/src/stores/workspace.ts`, `frontend/src/components/workflow/__tests__/ToolResultViewer.spec.ts`, `docs/superpowers/reports/2026-07-11-agent-tool-flow-system-evaluation.md` | Backend full suite -> 99 passed, 3 warnings; frontend full unit suite -> 15 files/72 tests passed; frontend build/type-check passed; JSON validation and `git diff --check` passed. |
| 05:14 | Completed v2 workflow/tool cleanup: removed DB service legacy agent helper dispatch, migrated v2 workflow execution to `ToolRegistry`, converted built-in templates to registered tool names, added v2 workflow registry execution coverage, and made LLM fallback tests deterministic when API keys are present. | `backend/app/services/workspace_db.py`, `backend/tests/test_workspace_api.py`, `backend/tests/test_llm.py`, `frontend/src/components/rag/KnowledgeConversationPanel.vue`, `task_plan.md`, `docs/superpowers/plans/2026-07-11-folder-agent-flow-completion.md` | Backend full suite rerun -> 100 passed, 3 warnings; frontend unit suite -> 15 files/72 tests passed; frontend build/type-check passed; JSON validation and `git diff --check` passed. |
| 05:22 | Planned production-grade LLM Agent tool-flow implementation: added phases for LLM tool-calling contract, iterative loop, real tool expansion, memory, UI, security, and 25-case evaluation. | `docs/superpowers/plans/2026-07-11-production-llm-agent-tool-flow.md`, `task_plan.md` | Planning only; no tests run. |
| 05:31 | Completed Phase 32 LLM tool-calling contract: added `AgentPlanner`, `ToolCallingLLM`, strict planner models, JSON fence/prefix repair, tool-name allowlist validation, deterministic fallback planning, and executor integration while preserving current v2 agent behavior. | `backend/app/services/agent_planner.py`, `backend/app/services/agent_executor.py`, `backend/tests/test_agent_planner.py`, `docs/superpowers/plans/2026-07-11-production-llm-agent-tool-flow.md`, `task_plan.md` | `PYTHONPATH=. uv run python -m pytest tests/test_agent_planner.py -q` -> 6 passed; focused v2 agent/tool API tests -> 5 passed. Initial parallel pytest run hit SQLite `database is locked`; rerun serially passed. |
| 05:42 | Completed the main Phase 33 iterative agent loop: executor now runs bounded plan-call-observe cycles, asks planner for revisions after tool failures or empty results, enforces max tool calls/retries/runtime, and records revision plans as visible plan steps. | `backend/app/services/agent_executor.py`, `backend/app/services/agent_planner.py`, `backend/tests/test_agent_executor.py`, `docs/superpowers/plans/2026-07-11-production-llm-agent-tool-flow.md`, `task_plan.md` | `PYTHONPATH=. uv run python -m pytest tests/test_agent_executor.py -q` -> 3 passed; `PYTHONPATH=. uv run python -m pytest tests/test_agent_planner.py -q` -> 6 passed. API-level cancel route remains follow-up; DB API tests not rerun because a user-running `backend/main.py` holds `backend/whucs.db`. |
| 05:58 | Finished Phase 33 cancel support: added `POST /api/v2/agents/tasks/{task_id}/cancel`, cancelled task status, persisted cancel step/audit log, generated frontend client, added workspace adapter and Pinia `cancelTask()`, and handled cancelled task progress in workflow view. | `backend/app/domain/workflow.py`, `backend/app/api/v2/knowledge.py`, `backend/app/services/workspace_db.py`, `backend/tests/test_openapi_export.py`, `frontend/src/client/workspace.ts`, `frontend/src/stores/agent.ts`, `frontend/src/stores/__tests__/agent.spec.ts`, `frontend/src/views/WorkflowBuilderView.vue`, `frontend/src/client/generated/*`, `frontend/src/client/openapi/workspace.openapi.json`, `docs/superpowers/plans/2026-07-11-production-llm-agent-tool-flow.md`, `task_plan.md` | Backend focused planner/executor/OpenAPI tests -> 10 passed; frontend agent store tests -> 4 passed; `pnpm type-check` passed. |
| 06:08 | Completed Phase 34 real tool expansion: added `rag_query`, `file_metadata_query`, whitelisted read-only `database_query`, and configured-provider-only `weather_lookup`; extended fallback planning and result views for the new tools. | `backend/app/services/tool_registry.py`, `backend/app/services/agent_planner.py`, `backend/app/services/agent_executor.py`, `backend/tests/test_tool_registry.py`, `backend/tests/test_agent_planner.py`, `docs/superpowers/plans/2026-07-11-production-llm-agent-tool-flow.md`, `task_plan.md` | `PYTHONPATH=. uv run python -m pytest tests/test_tool_registry.py tests/test_agent_planner.py tests/test_agent_executor.py tests/test_openapi_export.py -q` -> 16 passed, 2 warnings. |
| 06:14 | Completed Phase 35 agent memory backend hardening: create/continue responses now reload persisted task detail with messages/tool-call snapshots/plan revisions, follow-ups keep compact conversation history, older turns are summarized, and direct-answer continuations use prior context without unsafe LLM-added tools. | `backend/app/services/workspace_db.py`, `backend/app/services/agent_executor.py`, `backend/app/services/agent_planner.py`, `backend/app/domain/schemas.py`, `backend/app/domain/__init__.py`, `backend/tests/test_workspace_api.py`, `task_plan.md`, `findings.md`, `progress.md` | New memory regression -> 1 passed; isolated SQLite API agent checks -> 5 passed; planner/executor/tool/OpenAPI checks -> 16 passed; `pnpm type-check` passed; `git diff --check` passed. Default `backend/whucs.db` API rerun skipped because existing `uv run main.py` processes hold the SQLite lock. |
| 06:26 | Advanced Phase 36 UI: added persisted agent task history API/client/store loading, task detail panel with conversations/tool calls/plan revisions, follow-up and cancel controls, and wired workflow view to load old tasks. | `backend/app/domain/workflow.py`, `backend/app/domain/schemas.py`, `backend/app/domain/__init__.py`, `backend/app/repositories/workflow.py`, `backend/app/services/workspace_db.py`, `backend/app/api/v2/knowledge.py`, `backend/tests/test_openapi_export.py`, `frontend/src/client/workspace.ts`, `frontend/src/stores/agent.ts`, `frontend/src/views/WorkflowBuilderView.vue`, `frontend/src/components/workflow/AgentTaskDetailPanel.vue`, `frontend/src/components/workflow/__tests__/AgentTaskDetailPanel.spec.ts`, `frontend/src/stores/__tests__/agent.spec.ts`, `frontend/src/client/generated/*`, `frontend/src/client/openapi/workspace.openapi.json` | Backend focused memory/OpenAPI tests -> 5 passed, 2 warnings; frontend workflow/agent tests -> 10 passed; `pnpm type-check` passed. |
| 06:31 | Completed Phase 36 UI polish: task detail now shows compact history shortcuts, conversation/tool/plan counts, total tool latency, history-summary tags, readable tool input/output summaries, and plan paths; execution timeline shows planned tools, retry count, latency, and output summaries. | `frontend/src/components/workflow/AgentTaskDetailPanel.vue`, `frontend/src/components/workflow/AgentExecutionTimeline.vue`, `frontend/src/components/workflow/__tests__/AgentTaskDetailPanel.spec.ts`, `frontend/src/components/workflow/__tests__/AgentExecutionTimeline.spec.ts`, `task_plan.md`, `findings.md`, `progress.md` | Workflow component tests -> 3 passed; agent store + workflow component tests -> 8 passed; `pnpm type-check` passed; `pnpm build` passed; `git diff --check` passed. |
| 06:34 | Completed Phase 37 tool-flow security/ops: added registry-level role allowlists, file/KB preflight access checks before execution, tool execution audit hooks, provider config validation, structured latency logging, and latency/status propagation into agent steps. | `backend/app/services/tool_registry.py`, `backend/app/services/agent_executor.py`, `backend/app/services/workspace_db.py`, `backend/tests/test_tool_registry.py`, `backend/tests/test_agent_executor.py`, `docs/superpowers/plans/2026-07-11-production-llm-agent-tool-flow.md`, `task_plan.md` | Backend focused registry/executor/planner/OpenAPI tests -> 18 passed, 2 warnings. |
| 06:41 | Completed Phase 38 evaluation/acceptance: added deterministic 25-case agent tool-flow evaluation covering direct, RAG, file, database, weather, CSV, multi-tool, multi-turn, clarification, no-result, permission-denied, and invalid-input paths; updated evaluation report with metrics and limitations. | `backend/tests/test_agent_evaluation.py`, `docs/superpowers/reports/2026-07-11-agent-tool-flow-system-evaluation.md`, `docs/superpowers/plans/2026-07-11-production-llm-agent-tool-flow.md`, `task_plan.md` | Agent focused backend suite -> 23 passed, 2 warnings. |
| 06:43 | Implemented remaining risk-confirmation slice: added `/api/v2/agents/tasks/plan` plan preview, risk scoring for planned tools, frontend preview adapter/store state, and `AgentTaskComposer` confirm-before-run UI for medium/high risk plans. | `backend/app/domain/workflow.py`, `backend/app/services/agent_executor.py`, `backend/app/services/workspace_db.py`, `backend/app/api/v2/knowledge.py`, `backend/tests/test_agent_executor.py`, `backend/tests/test_openapi_export.py`, `frontend/src/client/workspace.ts`, `frontend/src/stores/agent.ts`, `frontend/src/stores/__tests__/agent.spec.ts`, `frontend/src/components/workflow/AgentTaskComposer.vue`, `frontend/src/views/WorkflowBuilderView.vue`, `frontend/src/client/generated/*`, `frontend/src/client/openapi/workspace.openapi.json` | Backend focused preview/OpenAPI tests -> 12 passed, 2 warnings; frontend agent store tests -> 6 passed; `pnpm type-check` passed. |
| 06:46 | Completed agent SSE stream slice: added `/api/v2/agents/tasks/stream`, SSE events for plan/call/observe/answer/done/error, frontend `streamAgentTask()` generator, Pinia streaming state/action, and workflow UI stream execution button. | `backend/app/services/workspace_db.py`, `backend/app/api/v2/knowledge.py`, `backend/tests/test_agent_memory.py`, `backend/tests/test_openapi_export.py`, `frontend/src/client/workspace.ts`, `frontend/src/stores/agent.ts`, `frontend/src/stores/__tests__/agent.spec.ts`, `frontend/src/components/workflow/AgentTaskComposer.vue`, `frontend/src/views/WorkflowBuilderView.vue`, `frontend/src/client/generated/*`, `frontend/src/client/openapi/workspace.openapi.json`, `docs/superpowers/plans/2026-07-11-production-llm-agent-tool-flow.md`, `task_plan.md` | Backend SSE/OpenAPI tests -> 6 passed, 2 warnings; frontend agent store tests -> 7 passed; `pnpm type-check` passed. |
| 06:58 | Completed final plan closure audit: no unchecked items remain in `task_plan.md` or the production agent plan, updated the evaluation report for risk-confirmation/SSE coverage, and ran full backend/frontend verification. | `docs/superpowers/reports/2026-07-11-agent-tool-flow-system-evaluation.md`, `findings.md`, `progress.md` | Backend full suite on initialized isolated SQLite DB -> 126 passed, 3 warnings; default `backend/whucs.db` full rerun hit SQLite lock from existing `uv run main.py`; frontend full unit suite -> 16 files/78 tests passed; `pnpm type-check`, `pnpm build`, buglog JSON validation, and `git diff --check` passed. |
| 11:06 | Fixed RAG answer quality and citation rendering: targeted retrieval now combines FAISS score with query-term reranking, LLM context includes source title/page/paragraph metadata, fallback/live answers preserve `[来源 N]` markers, and frontend citation markers render as styled anchors to citation cards. | `backend/app/services/rag_pipeline.py`, `backend/app/services/llm.py`, `backend/tests/test_rag_pipeline.py`, `backend/tests/test_llm.py`, `frontend/src/composables/useMarkdown.ts`, `frontend/src/composables/__tests__/useMarkdown.spec.ts`, `frontend/src/components/rag/KnowledgeConversationPanel.vue`, `frontend/src/components/rag/__tests__/KnowledgeConversationPanel.spec.ts` | RAG/LLM backend tests -> 7 passed; backend knowledge API slice -> 8 passed, 56 deselected, 3 warnings; frontend RAG markdown/component tests -> 5 passed; `git diff --check` passed. `pnpm type-check` still fails on pre-existing TeamChat/workspace message typing errors. |
| 11:14 | Tightened RAG file-overview prompting after real output showed “无法讲解这些文件”: single-file overview now uses document-overview mode, prompts forbid “未列出具体文件/资料不足” when document context exists, bare `来源 1` markers are normalized or rendered as citation links, and tests cover these regressions. | `backend/app/services/llm.py`, `backend/app/services/rag_pipeline.py`, `backend/tests/test_llm.py`, `backend/tests/test_rag_pipeline.py`, `frontend/src/composables/useMarkdown.ts`, `frontend/src/composables/__tests__/useMarkdown.spec.ts` | Backend RAG/LLM tests -> 10 passed; frontend RAG markdown/component tests -> 6 passed; `git diff --check` and buglog JSON validation passed. `pnpm type-check` still fails on pre-existing TeamChat/workspace message typing errors. |
| 11:46 | Fixed missing RAG citation cards after streaming: SSE citation events now include full citation fields, the knowledge store carries streaming citations into the final assistant message and migrates pending messages to the real conversation id, and the conversation panel renders streaming citation cards with real page/paragraph metadata. | `backend/app/services/workspace_db.py`, `frontend/src/client/workspace.ts`, `frontend/src/stores/knowledge.ts`, `frontend/src/stores/__tests__/knowledge.spec.ts`, `frontend/src/components/rag/KnowledgeConversationPanel.vue`, `frontend/src/components/rag/__tests__/KnowledgeConversationPanel.spec.ts` | Frontend RAG store/component/markdown tests -> 17 passed; backend RAG/LLM/API slice -> 12 passed, 62 deselected, 3 warnings; `git diff --check` and buglog JSON validation passed. `pnpm type-check` still fails only on pre-existing TeamChat/workspace message typing errors. |
| 2026-07-16 | Started advanced Vue Flow node implementation as Phases 46-48; audited the v2 DB executor, validator, debugger, codec, designer, palette, canvas, and inspector, and fixed the semantic boundary before coding. | `task_plan.md`, `findings.md`, `progress.md` | Planning/audit only. |
| 2026-07-16 | Completed advanced v2 DB workflow nodes end to end: real condition routing, safe transform, bounded loop projection, aggregation, authoritative validation, shared formal/debug behavior, Vue Flow palette/handles/inspector, lossless codec, debug inputs, generated client, and regressions. | `backend/app/api/v2/workflow.py`, `backend/app/services/workspace_db.py`, `backend/tests/test_workspace_api.py`, `frontend/src/components/workflow/*`, `frontend/src/composables/useWorkflowDesigner.ts`, `frontend/src/views/WorkflowBuilderView.vue`, `frontend/src/client/*`, planning files | Focused backend 9 passed; focused frontend 13 passed; backend full 147 passed; frontend full 27 files/112 tests passed; type-check, production build, OpenAPI generation, and `git diff --check` passed. |
| 2026-07-16 | Completed durable v2 workflow debugging: replaced process memory with DB-backed graph snapshots/session context, added repository/model/migration, preserved start/step/cancel API behavior, and repaired clean Alembic SQLite deployment. | `backend/app/models/workflow.py`, `backend/app/repositories/workflow.py`, `backend/app/services/workspace_db.py`, `backend/alembic/env.py`, `backend/alembic/versions/423efa013cf2_add_owner_id_to_files_folders.py`, `backend/alembic/versions/20260716_workflow_debug_sessions.py` | Clean Alembic upgrade reached `20260716wfdebug (head)`; migrated-DB workflow slice 6 passed; backend full suite 147 passed; diff check passed. |
| 2026-07-16 | Hardened durable debug concurrency with atomic expiring leases, overlap/cancel conflict responses, exception release, and abandoned-lease recovery. | `backend/app/models/workflow.py`, `backend/app/repositories/workflow.py`, `backend/app/services/workspace_db.py`, `backend/alembic/versions/20260716_workflow_debug_sessions.py`, `backend/tests/test_workspace_api.py` | Clean Alembic upgrade reached head; focused lease/debug tests 4 passed; backend full suite 148 passed; diff check passed. |
| 2026-07-16 | Completed branch skip observability: v2 executions, history, and debugging now return complete ordered traces with explicit skipped records; Vue Flow and panels render the state without reimplementing branch logic. | `backend/app/domain/workflow.py`, `backend/app/services/workspace_db.py`, `backend/tests/test_workspace_api.py`, `frontend/src/client/*`, `frontend/src/components/workflow/*`, `frontend/src/views/WorkflowBuilderView.vue`, `frontend/src/stores/workspace.ts` | Backend workflow slice 6 passed and full suite 148 passed; frontend 28 files/114 tests passed; type-check, build, client generation, and diff check passed. |
| 2026-07-16 | Audited and planned frontend fixes for protected-route enforcement, Vue Flow keyboard deletion, and viewport-bounded canvas layout. | `frontend/src/router/index.ts`, `frontend/src/stores/auth.ts`, `frontend/src/components/workflow/WorkflowCanvas.vue`, `frontend/src/composables/useWorkflowDesigner.ts`, `frontend/src/layouts/DesktopWorkspaceLayout.vue`, planning files | Planning only; implementation deferred until requested. |
| 2026-07-16 | Completed Phase 52: protected routes now require server-verified sessions with refresh recovery, Vue Flow supports focus-scoped Delete/Backspace through designer actions, and the canvas is viewport-bounded on desktop with a separate mobile height. | `frontend/src/stores/auth.ts`, `frontend/src/router/index.ts`, `frontend/src/components/workflow/WorkflowCanvas.vue`, `frontend/src/views/WorkflowBuilderView.vue`, `frontend/src/layouts/DesktopWorkspaceLayout.vue`, frontend tests | Focused 17 tests passed; full frontend 29 files/119 tests passed; type-check and production build passed; Chromium E2E 2/2 passed; diff check passed. |
