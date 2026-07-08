# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-07-08

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->
- Frontend UI should primarily use Naive UI components.
- CSS should use UnoCSS utilities as much as practical; minimize handwritten CSS.
- Suitable dependencies may be added when they improve correctness or maintainability.
- Backend commands should be run from `backend/` and use `uv`.
- Frontend `layouts/` should contain separate desktop/mobile layout shells; route/page composition belongs in `views/`.

## Key Learnings

- **Project:** whucs-training-project
- **Project docs:** Requirements deliverables for this course project can be placed under `report/requirements/`; the main project theme is a large-model intelligent file management and agent collaboration platform combining file management, RAG, visual workflows, RBAC, and team collaboration.
- **Open Design config:** For this project, Open Design integration is project-level: root `DESIGN.md` supplies the active design system and `skills/` supplies committed project skills; the system `od` binary may be GNU coreutils, so verify the Open Design CLI before running `od mcp install codex`.
- **Frontend MVP pattern:** The workbench root route uses Vue 3 + Vite + Pinia + Naive UI + UnoCSS. `WorkspaceView.vue` composes feature components from `frontend/src/components/workspace/`, chooses desktop/mobile shells from `frontend/src/layouts/`, and gets typed demo/client data from `frontend/src/client/workspace.ts` through `frontend/src/stores/workspace.ts`.
- **Frontend architecture boundary:** Keep frontend top-level `src/` limited to `assets/`, `auth/`, `client/`, `components/`, `composables/`, `layouts/`, `plugins/`, `router/`, `stores/`, `views/`, `App.vue`, and `main.ts`. `client/` is the future `@hey-api/openapi-ts` generation target after backend OpenAPI work; `auth/` remains a separate permission/session module linked to `client/`.
- **OpenAPI client generation:** `frontend/openapi-ts.config.ts` reads `src/client/openapi/workspace.openapi.json` and writes generated SDK/types to `src/client/generated/`; `pnpm generate:client` runs backend export with `uv run --no-project --with fastapi --with python-multipart` before `openapi-ts`.
- **Generated client integration:** `frontend/src/client/workspace.ts` is the hand-written page adapter and demo-data owner, but live API calls should go through `@/client/generated` SDK functions with auth headers from `src/auth/`.
- **Auth boundary:** `frontend/src/auth/` owns session persistence and auth header helpers; `frontend/src/stores/auth.ts` owns generated-client login/register/session restore state; routes use auth guard logic without moving permission state into `client/` or `views/`.
- **Refresh-token boundary:** Backend auth tokens carry a token kind, and the MVP enforces refresh tokens only on `/auth/refresh` while protected resources require access tokens. Frontend refresh calls must go through the generated SDK from `src/stores/auth.ts` and persist the rotated session via `src/auth/`.
- **Profile maintenance boundary:** `PATCH /api/v1/users/me` is the FR-U04 profile contract. Backend service validates duplicate emails and records `user.update_profile`; frontend calls `updateMeApiV1UsersMePatch` only from `stores/auth.ts`, while the page is `views/ProfileView.vue`.
- **Login lockout boundary:** FR-U05 is implemented in the in-memory auth service as a 5-failure, 5-minute lockout with structured `ACCOUNT_LOCKED` details and audit events. Frontend displays this through `stores/auth.ts`; `LoginView.vue` remains a thin presenter.
- **File lifecycle boundary:** File download/delete routes are backend file-domain actions with audit events. Frontend calls generated SDK functions through `src/client/workspace.ts`, keeps token helpers in `src/auth/`, owns state in `stores/workspace.ts`, and leaves `FileWorkbench.vue` as a Naive UI presenter that emits row actions.
- **File search/upload boundary:** Existing backend list/upload contracts are surfaced through generated SDK adapters in `src/client/workspace.ts`; filters and upload state live in `stores/workspace.ts`, `FileWorkbench.vue` remains a presenter, and upload controls are isolated in `FileUploadPanel.vue`.
- **File move/copy/version boundary:** FR-F01/FR-F05 lifecycle operations now use backend `PATCH /files/{file_id}`, `POST /files/{file_id}/copy`, `GET /files/{file_id}/versions`, and restore routes. Frontend maps generated snake_case contracts in `src/client/workspace.ts`, owns loading state in `stores/workspace.ts`, and keeps the lifecycle UI isolated in `FileLifecyclePanel.vue`.
- **Folder CRUD boundary:** FR-F02 folder create/tree/move/delete is now a backend/OpenAPI/generated-client/store/UI slice. Components emit camelCase payloads (`parentId`), `src/client/workspace.ts` maps them to OpenAPI `parent_id`, and `stores/workspace.ts` owns the tree, active folder, folder options, and loading state.
- **Folder move rule:** Backend folder moves cannot cross personal/team scope and cannot target self/descendants. Frontend move options should filter by same scope and exclude the active folder subtree before emitting updates.
- **Local API proxy boundary:** Vite development should proxy same-origin `/api` calls to `http://127.0.0.1:8000`; this keeps the generated client on `baseUrl: '/'` while connecting to the FastAPI backend during local development.
- **Testing pattern:** When mounting Naive UI workspace views in Vitest, install the Naive UI plugin and wrap the tested component in `NConfigProvider`; `@pinia/testing` needs `createSpy: vi.fn` in this setup.
- **UnoCSS gotcha:** Use arbitrary unitless line-height syntax (`leading-[1.65]`) for design line-height values. Classes like `leading-1.65` can generate tiny rem line heights and visually overlap text.
- **Responsive table gotcha:** Naive UI `NDataTable` can expand the mobile page if its columns require a wider table. Use `scroll-x` and constrain card/grid wrappers with `min-w-0 overflow-hidden`.
- **Mobile design gotcha:** For DESIGN.md phone behavior, do not stop at horizontal scrolling for operational tables. Keep `NDataTable` on wider screens, but render grouped mobile rows for files and other daily-use entities.

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->
- [2026-07-07] Skill path names may differ from displayed names; verify actual skill directory paths before reading `SKILL.md`.
- [2026-07-07] `frontend-skill` is not a current `openai/skills` curated skill name; list available curated skills before retrying or ask for a GitHub URL/path.
- [2026-07-08] Do not leave Vue starter tests or views after deleting starter components; `vue-tsc --build` still compiles stale files even when they are not routed.
- [2026-07-08] Do not rely on screenshots alone for mobile layout; also check `documentElement.scrollWidth > clientWidth` to catch horizontal overflow.
- [2026-07-08] The shell environment has `python3` but not `python`; use `python3` for local validation commands.
- [2026-07-08] Do not satisfy the phone table requirement only with `scroll-x`; when `DESIGN.md` says tables become grouped rows, add a mobile list/row representation.
- [2026-07-08] When restructuring frontend tests from inside `frontend/`, use paths relative to `frontend/`; `frontend/src/...` is wrong from that working directory.
- [2026-07-08] Avoid importing `@vueuse/core` only for a tiny media query in this Vite 8/Rolldown setup; it can add dependency annotation warnings. A focused local composable is cleaner here.
- [2026-07-08] When exporting OpenAPI for hey-api from a local JSON file, set FastAPI `servers=[{"url": "/"}]`; otherwise generated fetch clients can infer a bad `baseUrl` such as `src` from the input path.
- [2026-07-08] Naive UI does not export `NSegmented` in this dependency set; use `NRadioGroup` with `NRadioButton` and `button-style="solid"` for segmented login/register controls.
- [2026-07-08] When adding refresh-token support, remember to regenerate `frontend/src/client/generated/`; otherwise the auth store cannot import `refreshApiV1AuthRefreshPost`.
- [2026-07-08] New generated-client endpoints must be regenerated before frontend store tests import them; `updateMeApiV1UsersMePatch` only appeared after `pnpm generate:client`.
- [2026-07-08] When shell-searching for Markdown text that contains backticks, use single quotes or escape the backticks; double quotes trigger command substitution.
- [2026-07-08] Do not use a boolean parameter to represent optional-vs-required token return contracts in TypeScript stores; split optional and required helpers so `vue-tsc` can prove generated SDK calls receive a string token.
- [2026-07-08] Do not reference local constants inside `withDefaults(defineProps())`; Vue hoists the props macro, so inline defaults or use imported constants that are safe at module scope.
- [2026-07-08] Do not rely on `array[0]` to narrow fixture types in strict TypeScript tests; find a stable item and throw if missing before passing it to typed APIs.
- [2026-07-08] Do not write frontend folder move tests or UI flows that move a personal folder under `team-root`; the backend intentionally rejects cross-scope moves with `FOLDER_SCOPE_MISMATCH`.
- [2026-07-08] When adding file lifecycle UI, wire both desktop table rows and mobile grouped rows with the same `manage-file-*` public test/action surface, then keep lifecycle form state in a child panel component.

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
- [2026-07-08] Kept the first frontend slice as a deterministic demo-backed workbench instead of wiring full storage/vector/LLM infrastructure; this matches the current tested backend MVP and keeps production integrations replaceable.
- [2026-07-08] Removed unused Vue starter views/tests after replacing the root route with the workspace; restoring starter components would keep dead UI in the app and weaken the build boundary.
- [2026-07-08] Split workspace layout into `DesktopWorkspaceLayout.vue` and `MobileWorkspaceLayout.vue`, leaving page composition in `views/WorkspaceView.vue`; this matches the user's architecture direction and keeps responsive shell concerns out of page views.
- [2026-07-08] Keep generated OpenAPI output isolated under `frontend/src/client/generated/` and the exported schema under `frontend/src/client/openapi/`; this lets `workspace.ts` remain a stable adapter while generated files can be overwritten safely.
- [2026-07-08] Added a protected-routing auth slice: `/login` stays in `views/`, `/` requires an auth session, and the auth store calls generated SDK endpoints for login, registration, and current-user restoration while workspace data continues to load through the workspace adapter.
- [2026-07-08] Added refresh-token rotation as a contract-level hardening slice before database persistence: refreshed tokens include a new `jti`, refresh tokens cannot access `/users/me`, and access tokens cannot call `/auth/refresh`.
- [2026-07-08] Added FR-U04 user profile maintenance as the next auth-domain slice: keep editable profile UI in `views/`, reuse the auth store for current-user state, and leave layout files as navigation shells only.
- [2026-07-08] Added FR-U05 login failure lockout before persistence: keep the policy local to the auth service for now, expose structured runtime/OpenAPI errors, and map them in the auth store instead of adding login-page-specific logic.
- [2026-07-08] Added file download/delete before persistent object storage: keep content bytes in memory now, expose stable REST/OpenAPI/generated-client contracts, and make object storage a later repository implementation detail.
- [2026-07-08] Added frontend file search/upload wiring before folder CRUD because backend list/upload contracts and generated SDK functions already existed; this improved the daily file workflow without expanding backend scope.
- [2026-07-08] Added FR-F02 folder CRUD/tree UI as the next file-domain slice: backend owns validation and audit events, generated SDK stays isolated under `client/generated/`, Pinia owns folder state, and `FolderTreePanel.vue` presents tree navigation, breadcrumbs, create, rename, move, and delete controls.
- [2026-07-08] Added FR-F01/FR-F05 file lifecycle/version UI after folder CRUD because rename/move/copy need valid folder targets. Backend owns folder-scope validation and version creation/restore semantics; frontend keeps `FileWorkbench.vue` as composition and moves form/detail markup into `FileLifecyclePanel.vue`.
