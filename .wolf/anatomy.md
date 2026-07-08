# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-07-06T13:47:40.809Z
> Files: 8 tracked | Anatomy hits: 0 | Misses: 0

## ./

- `CLAUDE.md` — OpenWolf (~57 tok)
- `DESIGN.md` — Open Design 项目设计系统，定义智能文件管理平台的视觉风格、组件、布局和响应式规则 (~1500 tok)
- `OPEN_DESIGN.md` — Open Design 使用说明，记录导入本项目、MCP 命令和推荐 prompt (~300 tok)
- `README.md` — Project documentation (~0 tok)
- `findings.md` — Persistent planning findings for the intelligent file workspace platform goal (~550 tok)
- `progress.md` — Persistent session progress log for the intelligent file workspace platform goal (~350 tok)
- `task_plan.md` — Persistent phased task plan for the intelligent file workspace platform goal (~650 tok)

## .claude/

- `settings.json` (~441 tok)

## .claude/rules/

- `openwolf.md` (~313 tok)

## .wolf/

- `OPENWOLF.md` — OpenWolf operating protocol for navigation, code generation, memory, bug logging, and design QC (~1200 tok)
- `anatomy.md` — Auto-maintained project file index and token estimates (~1200 tok)
- `buglog.json` — Structured bug and failure log for repeated issues and fixes (~3000 tok)
- `cerebrum.md` — Long-term project/user preference memory and decision log (~1000 tok)
- `memory.md` — Session action log with one-line records after significant actions (~1200 tok)

## backend/

- `.gitignore` — Python/uv generated ignore rules for bytecode, virtualenvs, build outputs, caches, and local env files (~700 tok)
- `app/__init__.py` — Backend package marker (~10 tok)
- `app/api/__init__.py` — API package marker (~10 tok)
- `app/api/routes.py` — FastAPI `/api/v1` routes for auth login/register/refresh, current-user profile update, files, RAG, tools, agents, workflows, teams, audit, and snapshot (~1900 tok)
- `app/domain/__init__.py` — Domain schema package marker (~10 tok)
- `app/domain/schemas.py` — Pydantic request/response schemas for the MVP API contracts, including auth login/register/refresh/profile payloads (~2300 tok)
- `app/main.py` — FastAPI application factory, CORS, health route, and structured workspace error handler (~350 tok)
- `app/openapi_export.py` — CLI/helper for exporting FastAPI OpenAPI JSON to the frontend client boundary (~250 tok)
- `app/services/__init__.py` — Service package marker (~10 tok)
- `app/services/workspace.py` — In-memory MVP domain service with demo auth, token-kind refresh rotation, profile updates, files, RAG citations, tools, agents, workflows, teams, and audit logs (~4700 tok)
- `main.py` — Uvicorn-compatible backend entry point importing `app.main:app` (~80 tok)
- `pyproject.toml` — Backend uv project metadata and production dependency list (~900 tok)
- `README.md` — Project documentation (~0 tok)
- `tests/test_openapi_export.py` — Backend OpenAPI export contract test for title, version, server URL, and workspace snapshot path (~180 tok)
- `tests/test_workspace_api.py` — Backend API contract tests for auth, refresh-token/profile boundaries, files, RAG, agent tools, and workflow MVP (~1850 tok)
- `uv.lock` — Backend uv lockfile (~large)

## frontend/

- `README.md` — Project documentation (~0 tok)
- `index.html` — Vite HTML shell with zh-CN language and intelligent workspace title (~80 tok)
- `openapi-ts.config.ts` — `@hey-api/openapi-ts` config generating SDK/types from `src/client/openapi` into `src/client/generated` (~80 tok)
- `package.json` — Frontend dependencies and scripts for Vite, Vue, Naive UI, Pinia, Vitest, Playwright, UnoCSS, and OpenAPI client generation (~650 tok)
- `pnpm-lock.yaml` — Frontend dependency lockfile (~large)
- `vite.config.ts` — Vite config using Vue, Vue JSX, Vue DevTools, UnoCSS, and `@` alias (~120 tok)
- `vitest.config.ts` — Vitest config merged with Vite using jsdom and excluding e2e tests (~120 tok)
- `uno.config.ts` — UnoCSS Wind3 config with project colors and utility shortcuts (~350 tok)
- `src/App.vue` — App-level Naive UI providers and Chinese locale wrapping the router view (~180 tok)
- `src/main.ts` — Vue app bootstrap importing global CSS, UnoCSS virtual CSS, and app plugin installer (~80 tok)
- `src/router/index.ts` — Vue Router factory/default router with protected workspace/profile routes, guest-only login route, and return-based auth guard (~360 tok)
- `src/router/__tests__/authGuard.spec.ts` — Router guard tests for protected workspace/profile redirects and local session restoration (~300 tok)
- `src/assets/base.css` — Minimal global reset, typography stack, app background, and root sizing (~320 tok)
- `src/assets/main.css` — Imports the global base CSS only (~10 tok)
- `src/auth/index.ts` — Auth module barrel for workspace access helpers (~20 tok)
- `src/auth/workspaceAccess.ts` — Workspace auth/session helpers, localStorage persistence, and authorization header creation for client integration (~350 tok)
- `src/client/index.ts` — Client module barrel, reserved for OpenAPI-generated client integration (~20 tok)
- `src/client/openapi/workspace.openapi.json` — Exported FastAPI OpenAPI schema consumed by `@hey-api/openapi-ts` (~large)
- `src/client/generated/client.gen.ts` — Auto-generated hey-api fetch client instance with same-origin base URL (~120 tok)
- `src/client/generated/index.ts` — Auto-generated barrel exporting SDK functions and OpenAPI-derived types (~900 tok)
- `src/client/generated/sdk.gen.ts` — Auto-generated typed SDK functions for `/api/v1` backend endpoints (~2400 tok)
- `src/client/generated/types.gen.ts` — Auto-generated TypeScript types from backend OpenAPI schemas (~5000 tok)
- `src/client/generated/client/*.ts` — Auto-generated hey-api fetch transport helpers and request types (~3000 tok)
- `src/client/generated/core/*.ts` — Auto-generated hey-api serializers, auth, path/query, SSE, and utility helpers (~3500 tok)
- `src/client/workspace.ts` — Workspace client adapter and demo data using generated OpenAPI types/SDK plus auth headers (~2600 tok)
- `src/components/workspace/AgentWorkflowPanel.vue` — Naive UI workflow/tool panel with registered tools and agent timeline (~450 tok)
- `src/components/workspace/FileWorkbench.vue` — Naive UI file table with tag filters, parse status chips, and grouped mobile file rows (~1100 tok)
- `src/components/workspace/RagInsightPanel.vue` — RAG answer panel with query alert, answer text, and citation list (~320 tok)
- `src/components/workspace/StatusChip.vue` — Shared semantic status chip using UnoCSS utilities (~180 tok)
- `src/components/workspace/SummaryStrip.vue` — Naive UI statistic cards for workspace summary counts (~280 tok)
- `src/components/workspace/TeamAuditPanel.vue` — Team collaboration and audit log side panels (~300 tok)
- `src/composables/useWorkspaceLayoutMode.ts` — Viewport media-query composable selecting desktop or mobile workspace layout (~200 tok)
- `src/composables/useWorkspaceNavigation.ts` — Workspace navigation items and API state label/type derivations (~350 tok)
- `src/layouts/DesktopWorkspaceLayout.vue` — Desktop/tablet workspace shell with sidebar navigation and top actions (~650 tok)
- `src/layouts/MobileWorkspaceLayout.vue` — Phone workspace shell with sticky top navigation and compact action header (~650 tok)
- `src/plugins/index.ts` — App plugin installer for Pinia, router, and Naive UI (~120 tok)
- `src/plugins/naive.ts` — Naive UI plugin installer and DESIGN.md theme overrides (~500 tok)
- `src/stores/auth.ts` — Pinia setup store for generated-client login/register/session restore/refresh/profile update, current user state, and local session persistence (~1050 tok)
- `src/stores/workspace.ts` — Pinia setup store for workspace snapshot, narrative, loading state, and demo/live/fallback modes using auth session tokens (~500 tok)
- `src/stores/__tests__/auth.spec.ts` — Store tests for generated-client login, registration, `/users/me` restoration/profile update, refresh-session rotation, and persisted auth headers (~1050 tok)
- `src/views/LoginView.vue` — Naive UI login/register view with JWT/RBAC/audit copy and protected-workspace redirect handling (~900 tok)
- `src/views/ProfileView.vue` — Protected Naive UI personal profile page for FR-U04 display name/email maintenance using auth store state (~1000 tok)
- `src/views/WorkspaceView.vue` — Route-level Chinese workbench page composing layouts, summary, files, RAG, agent/workflow, team, and audit panels (~700 tok)
- `src/views/__tests__/LoginView.spec.ts` — Login view blackbox render test with Naive UI provider, router, and Pinia test setup (~350 tok)
- `src/views/__tests__/ProfileView.spec.ts` — Profile view test for protected profile rendering and update form submission through the auth store (~500 tok)
- `src/views/__tests__/WorkspaceView.spec.ts` — Frontend blackbox test for the report-aligned intelligent workspace view with Naive UI and Pinia test setup (~500 tok)
- `tests/frontendArchitecture.spec.ts` — Architecture boundary test for agreed frontend directories, split layouts, no services, and generated client wiring (~650 tok)

## frontend deleted starter files/

- `src/components/HelloWorld.vue` — Removed unused Vue starter component after replacing the app with the workspace.
- `src/components/TheWelcome.vue` — Removed unused Vue starter component after replacing the app with the workspace.
- `src/components/WelcomeItem.vue` — Removed unused Vue starter component after replacing the app with the workspace.
- `src/components/__tests__/HelloWorld.spec.ts` — Removed stale starter test that referenced deleted starter components.
- `src/assets/logo.svg` — Removed unused Vue starter logo after app shell replacement.
- `src/components/icons/*.vue` — Removed unused Vue starter icon components after app shell replacement.
- `src/services/workspaceApi.ts` — Replaced by `src/client/workspace.ts` as the temporary client boundary.
- `src/stores/counter.ts` — Removed unused Vue starter counter store.
- `src/views/AboutView.vue` — Removed unused Vue starter route view.
- `src/views/HomeView.vue` — Removed unused Vue starter route view that referenced deleted starter components.

## references/

- `base.md` (~1820 tok)

## report/before/

- `plan_closed.tex` (~5046 tok)

## report/requirements/

- `requirements_specification.md` — 需求规格说明书，含用户需求、PlantUML 需求模型、ER 图、数据字典、非功能需求和依赖项 (~22000 tok)

## report/design/

- `system_design_specification.md` — 系统设计说明书，含架构、API 合约、模块边界、UI 布局和部署设计 (~24000 tok)

## skills/

- `whu-intelligent-file-workspace/SKILL.md` — Open Design 项目专用 prototype skill，面向文件管理、RAG、Agent、工具流、团队协作和权限页面原型 (~900 tok)
