# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-07-10T13:21:21.185Z
> Files: 180 tracked | Anatomy hits: 0 | Misses: 0

## ../.claude/plans/

- `eventual-rolling-stardust.md` — Phase 25: Document Parser Integration & Verification (~591 tok)

## ./

- `CLAUDE.md` — OpenWolf (~57 tok)
- `DESIGN.md` — Open Design 项目设计系统，定义智能文件管理平台的视觉风格、组件、布局和响应式规则 (~1500 tok)
- `findings.md` — Findings & Decisions (~5086 tok)
- `OPEN_DESIGN.md` — Open Design 使用说明，记录导入本项目、MCP 命令和推荐 prompt (~300 tok)
- `progress.md` — Progress Log (~20740 tok)
- `README.md` — Project documentation (~0 tok)
- `task_plan.md` — Task Plan: Intelligent File Workspace Platform (~7507 tok)

## .claude/

- `settings.json` (~441 tok)

## .claude/rules/

- `openwolf.md` (~313 tok)

## .github/workflows/

- `ci.yml` — CI: CI (~297 tok)

## .wolf/

- `anatomy.md` — Auto-maintained project file index and token estimates (~1200 tok)
- `buglog.json` — Structured bug and failure log for repeated issues and fixes (~3000 tok)
- `cerebrum.md` — Long-term project/user preference memory and decision log (~1000 tok)
- `memory.md` — Session action log with one-line records after significant actions (~1200 tok)
- `OPENWOLF.md` — OpenWolf operating protocol for navigation, code generation, memory, bug logging, and design QC (~1200 tok)

## backend/

- `.gitignore` — Python/uv generated ignore rules for bytecode, virtualenvs, build outputs, caches, and local env files (~700 tok)
- `app/__init__.py` — Backend package marker (~10 tok)
- `app/api/__init__.py` — API package marker (~10 tok)
- `app/api/routes.py` — Legacy monolithic FastAPI `/api/v1` routes (deprecated in favor of v1/ split) (~2900 tok)
- `app/domain/__init__.py` — Domain schema package marker (~10 tok)
- `app/domain/schemas.py` — Pydantic request/response schemas for the MVP API contracts, including auth login/register/refresh/profile, folder/file payloads, annotations, notifications, teams, workflows, knowledge bases, and permission rules (~3400 tok)
- `app/main.py` — FastAPI application factory, CORS, health route, and structured workspace error handler (~350 tok)
- `app/openapi_export.py` — CLI/helper for exporting FastAPI OpenAPI JSON to the frontend client boundary (~250 tok)
- `app/services/__init__.py` — Service package marker (~10 tok)
- `app/services/parser.py` — Multi-format document parser (PDF/DOCX/PPTX/TXT/MD/CSV) with lazy-loaded extractors, segment metadata, and ParseError handling (~200 tok)
- `app/services/workspace.py` — In-memory MVP domain service with demo auth, token-kind refresh rotation, profile updates, folder tree CRUD, files, annotations, notifications/unread counts, RAG citations, tools, agents, workflows, teams, ACL permission rules, audit logs, and integrated document parser (~8200 tok)
- `main.py` — Uvicorn-compatible backend entry point importing `app.main:app` (~80 tok)
- `pyproject.toml` — Add your description here (~266 tok)
- `README.md` — Project documentation (~0 tok)
- `tests/test_openapi_export.py` — Backend OpenAPI export contract test for title, version, server URL, workspace snapshot, folder CRUD paths, file lifecycle/annotation/notification paths, workflow paths, team paths, and permission rule paths (~600 tok)
- `tests/test_parser.py` — Parser unit tests: 21 tests covering 6 formats (PDF/DOCX/PPTX/TXT/MD/CSV), format detection, error handling, and segment metadata (~400 tok)
- `tests/test_workspace_api.py` — Backend API contract tests for auth, refresh-token/profile boundaries, folder CRUD/tree validations, file lifecycle/versioning, files, annotations, notifications, RAG, agent tools, workflow MVP, team RBAC, and ACL permission rules (~4200 tok)

## backend/alembic/

- `env.py` — this is the Alembic Config object, which provides (~680 tok)

## backend/app/

- `main.py` — API: 1 endpoints (~1173 tok)
- `openapi_export.py` — export_openapi, main (~229 tok)

## backend/app/api/

- `routes.py` — Legacy monolithic routes file (deprecated in favor of v1/ split) (~6965 tok)

## backend/app/api/v1/

- `__init__.py` — Aggregator APIRouter(prefix="/api/v1") including all domain routers (~200 tok)
- `admin.py` — Permission rules CRUD, notifications, audit logs, workspace snapshot, WebSocket (~800 tok)
- `auth.py` — current_user dependency, register/login/refresh, users/me profile endpoints (~300 tok)
- `files.py` — File CRUD, upload/multipart upload, annotations, share links, download, versions, recycle bin (~2200 tok)
- `folders.py` — Folder tree, create/update/delete folder endpoints (~200 tok)
- `knowledge.py` — Knowledge base CRUD, document management, QA query/stream, tools, agent tasks (~600 tok)
- `teams.py` — Team CRUD, messages, invites, members, join/leave endpoints (~800 tok)
- `workflow.py` — Workflow CRUD, validate, publish, execute endpoints (~400 tok)

## backend/app/api/v2/

- `__init__.py` (~230 tok)
- `_deps.py` — WorkspaceServiceDB factory (get_svc) and current_user JWT dependency (~450 tok)
- `admin.py` — API: 6 endpoints (~730 tok)
- `auth.py` — API: 5 endpoints (~684 tok)
- `files.py` — API: 19 endpoints (~2341 tok)
- `folders.py` — API: 4 endpoints (~463 tok)
- `general.py` — API: 2 endpoints, workspace snapshot and health (~250 tok)
- `knowledge.py` — API: 8 endpoints (~941 tok)
- `teams.py` — API: 12 endpoints (~1334 tok)
- `workflow.py` — API: 6 endpoints (~721 tok)

## backend/app/core/

- `config.py` — Declares Settings (~264 tok)

## backend/app/domain/

- `__init__.py` — Domain schemas for API contracts. (~690 tok)
- `auth.py` — Pydantic: UserCreate (~300 tok)
- `common.py` — Pydantic: ErrorResponse (~700 tok)
- `file.py` — Pydantic: FileItem (~1003 tok)
- `folder.py` — Pydantic: FolderItem (~206 tok)
- `knowledge.py` — Pydantic: Citation (~503 tok)
- `schemas.py` — Backward-compatible re-exports from domain-specific schema modules. (~746 tok)
- `team.py` — Pydantic: TeamMessageCreate (~666 tok)
- `workflow.py` — Pydantic: ToolDefinition (~1073 tok)

## backend/app/models/

- `file.py` — Declares File (~650 tok)
- `folder.py` — Declares Folder (~365 tok)

## backend/app/services/

- `embedding.py` — Semantic embedding service wrapping sentence-transformers. (~576 tok)
- `llm.py` — LLM service — OpenAI-compatible multi-provider with graceful fallback. (~1261 tok)
- `parser.py` — Multi-format document text extraction for the knowledge-base pipeline. (~2386 tok)
- `websocket_manager.py` — WebSocket connection manager for real-time push. (~424 tok)
- `workspace_db.py` — WorkspaceService backed by SQLAlchemy — full DB migration. (~7167 tok)
- `workspace.py` — WorkspaceError: register_user, register_user_db, login_user (~37009 tok)

## backend/tests/

- `test_embedding.py` — Tests for the embedding service. (~934 tok)
- `test_llm.py` — Tests for the LLM service with graceful fallback. (~435 tok)
- `test_parser.py` — Tests for the multi-format document parser. (~2125 tok)
- `test_workspace_api.py` — auth_session, auth_headers, upload_test_file, create_test_folder (~22900 tok)

## docs/superpowers/specs/

- `2026-07-10-file-manager-refactor-design.md` — File Manager Refactor — Design Spec (~938 tok)

## frontend deleted starter files/


## frontend/

- `index.html` — Vite HTML shell with zh-CN language and intelligent workspace title (~80 tok)
- `openapi-ts.config.ts` — `@hey-api/openapi-ts` config generating SDK/types from `src/client/openapi` into `src/client/generated` (~80 tok)
- `package.json` — Frontend dependencies and scripts for Vite, Vue, Naive UI, Pinia, Vitest, Playwright, UnoCSS, and OpenAPI client generation via backend `uv`/`python3` export (~650 tok)
- `README.md` — Project documentation (~0 tok)
- `src/App.vue` — App-level Naive UI providers and Chinese locale wrapping the router view (~180 tok)
- `src/assets/base.css` — Minimal global reset, typography stack, app background, and root sizing (~320 tok)
- `src/assets/main.css` — Imports the global base CSS only (~10 tok)
- `src/auth/index.ts` — Auth module barrel for workspace access helpers (~20 tok)
- `src/auth/workspaceAccess.ts` — Workspace auth/session helpers, localStorage persistence, and authorization header creation for client integration (~350 tok)
- `src/client/generated/client.gen.ts` — Auto-generated hey-api fetch client instance with same-origin base URL (~120 tok)
- `src/client/generated/client/*.ts` — Auto-generated hey-api fetch transport helpers and request types (~3000 tok)
- `src/client/generated/core/*.ts` — Auto-generated hey-api serializers, auth, path/query, SSE, and utility helpers (~3500 tok)
- `src/client/generated/index.ts` — Auto-generated barrel exporting SDK functions and OpenAPI-derived types (~900 tok)
- `src/client/generated/sdk.gen.ts` — Auto-generated typed SDK functions for `/api/v1` backend endpoints, including annotation and notification contracts (~2600 tok)
- `src/client/generated/types.gen.ts` — Auto-generated TypeScript types from backend OpenAPI schemas, including notification item/list response types (~5600 tok)
- `src/client/index.ts` — Client module barrel, reserved for OpenAPI-generated client integration (~20 tok)
- `src/client/workspace.ts` — Workspace client adapter and demo data using generated OpenAPI types/SDK for snapshot, folder tree/CRUD, file list/upload/download/delete/update/copy/version restore, annotations, notifications, knowledge bases, workflows, teams, permission rules, and auth headers (~5600 tok)
- `src/components/workspace/__tests__/FileAnnotationPanel.spec.ts` — File annotation panel blackbox test for escaped rendering and create/reply/delete emits (~650 tok)
- `src/components/workspace/__tests__/FileWorkbench.spec.ts` — File workbench blackbox test for search/upload controls, row download/delete actions, lifecycle management, copy, and version restore emits (~850 tok)
- `src/components/workspace/__tests__/FolderTreePanel.spec.ts` — Folder tree panel blackbox test for tree rendering, breadcrumbs, select, create, rename, and delete events (~650 tok)
- `src/components/workspace/__tests__/NotificationInboxPanel.spec.ts` — Notification inbox panel blackbox test for unread/read rendering and mark-read emits (~350 tok)
- `src/components/workspace/__tests__/PermissionRulesPanel.spec.ts` — Permission rules panel blackbox test for inherited deny/file override rendering and create/delete emits (~500 tok)
- `src/components/workspace/AgentWorkflowPanel.vue` — Naive UI workflow/tool panel with registered tools and agent timeline (~450 tok)
- `src/components/workspace/CategorySidebar.vue` — Baidu Wangpan-style category sidebar with type filters (全部文件/图片/文档/视频/其他/共享/回收站) and NTree folder tree, replacing FolderTreePanel (~900 tok)
- `src/components/workspace/FileAnnotationPanel.vue` — Naive UI + UnoCSS file annotation presenter for creating annotations, replying, deleting, and showing nested replies (~1200 tok)
- `src/components/workspace/FileLifecyclePanel.vue` — Naive UI + UnoCSS file lifecycle panel for rename, move, tags, copy creation, version listing, and rollback emits (~1300 tok)
- `src/components/workspace/FileUploadModal.vue` — NModal-based file upload dialog with drag-drop NUpload, NTreeSelect folder picker, and NDynamicTags tag input (~800 tok)
- `src/components/workspace/FileUploadPanel.vue` — Naive UI upload panel for file, dynamic target folder options, and tag input, emitting typed upload payloads (~450 tok)
- `src/components/workspace/FileWorkbench.vue` — Naive UI file workbench composing folder tree, search filters, upload panel, lifecycle panel, permission rules panel, row actions, parse status chips, and grouped mobile file rows (~2500 tok)
- `src/components/workspace/FolderTreePanel.vue` — Naive UI + UnoCSS folder tree/breadcrumb panel for create, rename, same-scope move, delete, and active folder selection (~1600 tok)
- `src/components/workspace/NotificationInboxPanel.vue` — Naive UI + UnoCSS notification inbox presenter for unread invites, mentions, annotation replies, workflow events, and mark-read emits (~700 tok)
- `src/components/workspace/PermissionRulesPanel.vue` — Naive UI + UnoCSS presenter for resource ACL rule list/create/delete, subject/resource/action/effect selection, and inherited/override labeling (~1600 tok)
- `src/components/workspace/RagInsightPanel.vue` — RAG answer panel with query alert, answer text, and citation list (~320 tok)
- `src/components/workspace/StatusChip.vue` — Shared semantic status chip using UnoCSS utilities (~180 tok)
- `src/components/workspace/SummaryStrip.vue` — Naive UI statistic cards for workspace summary counts (~280 tok)
- `src/components/workspace/TeamAuditPanel.vue` — Team collaboration, notification inbox composition, and audit log side panels (~500 tok)
- `src/composables/useWorkspaceLayoutMode.ts` — Viewport media-query composable selecting desktop or mobile workspace layout (~200 tok)
- `src/composables/useWorkspaceNavigation.ts` — Workspace navigation items and API state label/type derivations (~350 tok)
- `src/layouts/DesktopWorkspaceLayout.vue` — Desktop/tablet workspace shell with sidebar navigation and top actions (~650 tok)
- `src/layouts/MobileWorkspaceLayout.vue` — Phone workspace shell with sticky top navigation and compact action header (~650 tok)
- `src/main.ts` — Vue app bootstrap importing global CSS, UnoCSS virtual CSS, and app plugin installer (~80 tok)
- `src/plugins/index.ts` — App plugin installer for Pinia, router, and Naive UI (~120 tok)
- `src/plugins/naive.ts` — Naive UI plugin installer and DESIGN.md theme overrides (~500 tok)
- `src/router/__tests__/authGuard.spec.ts` — Router guard tests for protected workspace/profile redirects and local session restoration (~300 tok)
- `src/router/index.ts` — Vue Router factory/default router with protected workspace/profile routes, guest-only login route, and return-based auth guard (~360 tok)
- `src/stores/__tests__/auth.spec.ts` — Store tests for generated-client login, registration, `/users/me` restoration/profile update, refresh-session rotation, and persisted auth headers (~1050 tok)
- `src/stores/__tests__/workspace.spec.ts` — Store tests for generated-client-backed folder CRUD/tree actions, file list/upload/download/delete/update/copy/version actions, annotations, notifications, knowledge/workflow/team actions, permission rules, and local snapshot updates (~2300 tok)
- `src/stores/auth.ts` — Pinia setup store for generated-client login/register/session restore/refresh/profile update, current user state, and local session persistence (~1050 tok)
- `src/stores/knowledge.ts` — Pinia setup store for knowledge base CRUD, document management, RAG question/answer, indexed files, and narrative state (~500 tok)
- `src/stores/permissions.ts` — Pinia setup store for workspace permission rules CRUD and ACL management (~200 tok)
- `src/stores/workspace.ts` — Pinia setup store for workspace snapshot, narrative, folder tree CRUD/selection/options, file filters/list/upload/download/delete/update/copy/version state, annotation/notification state/actions, knowledge/workflow/team state, permission rule state/actions, and demo/live/fallback modes using auth session tokens (~3400 tok)
- `src/views/__tests__/LoginView.spec.ts` — Login view blackbox render test with Naive UI provider, router, and Pinia test setup (~350 tok)
- `src/views/__tests__/ProfileView.spec.ts` — Profile view test for protected profile rendering and update form submission through the auth store (~500 tok)
- `src/views/__tests__/WorkspaceView.spec.ts` — Frontend blackbox test for the report-aligned intelligent workspace view, RAG/workflow/team/permission wiring, and Naive UI/Pinia test setup (~750 tok)
- `src/views/LoginView.vue` — Naive UI login/register view with JWT/RBAC/audit copy and protected-workspace redirect handling (~900 tok)
- `src/views/ProfileView.vue` — Protected Naive UI personal profile page for FR-U04 display name/email maintenance using auth store state (~1000 tok)
- `src/views/WorkspaceView.vue` — Route-level Chinese workbench page composing layouts, summary, folder/file lifecycle/permission workbench, RAG, agent/workflow, team notification, and audit panels (~1400 tok)
- `tests/frontendArchitecture.spec.ts` — Architecture boundary test for agreed frontend directories, split layouts, no services, and generated client wiring (~650 tok)
- `uno.config.ts` — UnoCSS Wind3 config with project colors and utility shortcuts (~350 tok)
- `vite.config.ts` — Vite config using Vue, Vue JSX, Vue DevTools, UnoCSS, and `@` alias (~120 tok)
- `vitest.config.ts` — Vitest config merged with Vite using jsdom and excluding e2e tests (~120 tok)

## frontend/src/auth/

- `workspaceAccess.ts` — Exports WorkspaceAuthSession, workspaceSessionStorageKey, createAuthorizationHeader, resolveWorkspaceToken, resolveOptionalAccessToken, requireAccessToken, localStorage helpers (~550 tok)

## frontend/src/client/

- `workspace.ts` — Exports AgentStep, WorkspaceFile, WorkspaceFileAnnotation, WorkspaceFileAnnotationReply + 56 more (~12430 tok)

## frontend/src/client/generated/

- `client.gen.ts` — The `createClientConfig()` function will be called on client initialization (~352 tok)

## frontend/src/components/files/

- `CategorySidebar.vue` — Vue: setup (~1161 tok)
- `FileDropdown.vue` — Vue: setup (~1256 tok)
- `FileWorkbench.vue` — Vue: setup (~4265 tok)

## frontend/src/components/team/

- `TeamAuditPanel.vue` — Vue: setup (~2812 tok)

## frontend/src/components/workflow/

- `AgentWorkflowPanel.vue` — Vue: setup (~3533 tok)

## frontend/src/components/workspace/

- `AgentWorkflowPanel.vue` — Vue: 选择文件, setup (~3776 tok)
- `CategorySidebar.vue` — Vue: setup (~976 tok)
- `FileDrawer.vue` — Vue: setup (~2517 tok)
- `FileDropdown.vue` — Vue: setup (~1147 tok)
- `FileUploadModal.vue` — Vue: setup (~1137 tok)
- `FileWorkbench.vue` — Vue: setup (~4202 tok)
- `TeamAuditPanel.vue` — Vue: setup (~2814 tok)

## frontend/src/components/workspace/__tests__/

- `AgentWorkflowPanel.spec.ts` — API routes: GET (9 endpoints) (~1389 tok)
- `PermissionRulesPanel.spec.ts` — API routes: GET (2 endpoints) (~906 tok)

## frontend/src/composables/

- `useMarkdown.ts` — Exports renderMarkdown (~249 tok)
- `useWorkspaceNavigation.ts` — Exports WorkspaceNavItem, useWorkspaceNavigation (~465 tok)

## frontend/src/layouts/

- `DesktopWorkspaceLayout.vue` — Vue: setup (~2320 tok)
- `MobileWorkspaceLayout.vue` — Vue: setup (~1704 tok)

## frontend/src/router/

- `index.ts` — Exports createAppRouter (~694 tok)

## frontend/src/stores/

- `auth.ts` — Exports LoginCredentials, RegisterCredentials, useAuthStore (~1652 tok)
- `knowledge.ts` — Exports useKnowledgeStore (~2431 tok)
- `permissions.ts` — Exports usePermissionsStore (~1040 tok)
- `workflowStore.ts` — Pinia setup store for workflow lifecycle with local state (activeWorkflowId, validation, execution, operationLoading, workflows list), computed activeWorkflow, and actions (list/create/update/validate/publish/execute) calling workspace client API with requireAccessToken (~3400 tok)
- `workspace.ts` — Exports WorkspaceApiState, useWorkspaceStore (~18171 tok)

## frontend/src/stores/__tests__/

- `workspace.spec.ts` — testFile: getTestFile (~10985 tok)

## frontend/src/views/

- `FileManagerView.vue` — Vue: setup (~1112 tok)
- `LoginView.vue` — Vue: setup (~1080 tok)
- `PermissionAuditView.vue` — Vue: setup (~901 tok)
- `ProfileView.vue` — Vue: setup (~1263 tok)
- `RagQaView.vue` — Vue: setup (~2026 tok)
- `TeamChatView.vue` — Vue: all, setup (~6106 tok)
- `WorkflowBuilderView.vue` — Vue: setup (~10454 tok)

## frontend/src/views/__tests__/

- `LoginView.spec.ts` — Declares TestHost (~363 tok)

## references/

- `base.md` (~1820 tok)

## report/before/

- `plan_closed.tex` (~5046 tok)

## report/design/

- `system_design_specification.md` — 基于大模型的智能文件管理与智能体协同平台系统设计说明书 (~11883 tok)

## report/requirements/

- `requirements_specification.md` — 需求规格说明书，含用户需求、PlantUML 需求模型、ER 图、数据字典、非功能需求和依赖项 (~22000 tok)

## skills/

- `whu-intelligent-file-workspace/SKILL.md` — Open Design 项目专用 prototype skill，面向文件管理、RAG、Agent、工具流、团队协作和权限页面原型 (~900 tok)
