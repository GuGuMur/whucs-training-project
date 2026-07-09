# Progress Log

## Session: 2026-07-08

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

## Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
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
| Where am I? | Phase 21 complete — remote merge with full-page views, guest auth, and permission audit integrated |
| Where am I going? | Persistent storage/vector indexing, persistent permission repositories/admin policy matrix, drag/drop workflow node editing (remote WorkflowBuilderView provides foundation), WebSocket collaboration, and live LLM/tool integrations |
| What's the goal? | Build the report-aligned intelligent file management and agent collaboration platform |
| What have I learned? | See `findings.md` |
| What have I done? | Completed a tested backend API skeleton with 24 tests, Vue/Naive UI workbench MVP, OpenAPI-to-generated-client workflow, auth guard/refresh/profile slices, login lockout, file CRUD/lifecycle/version UI, folder tree, team membership/invites/permissions, knowledge-base/RAG CRUD, editable workflow definitions, cross-resource RBAC, resource ACL rules with permission panel. Merged remote contributions: WorkflowBuilderView, TeamChatView, RagQaView, PermissionAuditView, guest login with role-based routing, and demo user seeding |
