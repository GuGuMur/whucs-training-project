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

## Resources
- `report/requirements/requirements_specification.md`
- `report/design/system_design_specification.md`
- `DESIGN.md`
- `skills/whu-intelligent-file-workspace/SKILL.md`
- `frontend/package.json`
- `backend/pyproject.toml`

## Visual/Browser Findings
- No browser screenshots inspected yet.
