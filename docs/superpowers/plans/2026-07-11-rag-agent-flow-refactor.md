# RAG And Agent Flow Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the current RAG Q&A and tool-flow modules into scoped knowledge-base management, multi-turn cited RAG, and a transparent "understand-call-observe-answer" agent execution flow.

**Architecture:** Keep the existing v2 FastAPI/OpenAPI/Pinia boundary and extend it incrementally. Split RAG state into `stores/knowledge.ts` and tool-flow state into `stores/workflow.ts` or a focused `stores/agent.ts`, while keeping generated SDK calls behind `frontend/src/client/workspace.ts` unless a matching generated-client adapter split is introduced consistently.

**Tech Stack:** FastAPI, SQLAlchemy async models, Alembic, Pydantic, FAISS embedding retrieval, OpenAI-compatible LLM fallback, Vue 3 `<script setup>`, Pinia, Naive UI, UnoCSS, Vitest, backend pytest.

---

## Current-State Anchors

- Backend RAG routes are in `backend/app/api/v2/knowledge.py`.
- RAG schemas are in `backend/app/domain/knowledge.py`.
- Tool and workflow schemas are in `backend/app/domain/workflow.py`.
- DB-backed service logic is concentrated in `backend/app/services/workspace_db.py`.
- Existing DB models include `backend/app/models/knowledge.py`, `backend/app/models/workflow.py`, and `backend/app/models/general.py`.
- Frontend adapters are in `frontend/src/client/workspace.ts`.
- Current standalone RAG page is `frontend/src/views/RagQaView.vue`.
- Current visual workflow page is `frontend/src/views/WorkflowBuilderView.vue`.
- Existing RAG store is `frontend/src/stores/knowledge.ts`, but `RagQaView.vue` still uses `useWorkspaceStore`.
- Existing workflow store is `frontend/src/stores/workflow.ts`, but `WorkflowBuilderView.vue` still has direct `fetch()` calls for debug endpoints.

## Target User Capabilities

- Users can create, edit, archive, and delete knowledge bases under personal or team scope.
- Users can classify knowledge bases with category and tags, and track freshness/indexing status.
- Users can batch add and remove files from a knowledge base.
- Users can ask multi-turn questions and see persisted question, answer, citations, and retrieved snippets.
- Retrieval filters by user/team permissions before embedding search.
- Tool-flow execution shows the full path: understanding, planning, tool call, observation, final answer.
- Tool-flow supports at least `calculator`, `course_lookup`, `file_content_search`, and `database_query` or `python_data`.
- Missing input, invalid tool parameters, tool failures, and no-result states return actionable Chinese prompts.

## File Structure

### Backend Files

- Modify: `backend/app/domain/knowledge.py`
  - Add scoped knowledge-base fields, batch file request/response schemas, conversation schemas, citation snapshot schemas, and clear QA error shape.
- Modify: `backend/app/domain/workflow.py`
  - Add structured tool definitions, agent task detail response, agent continuation request, and explicit execution phase values.
- Modify: `backend/app/models/knowledge.py`
  - Add columns for scope/category/tags/freshness and add conversation/message/citation snapshot tables if they stay in the knowledge domain.
- Modify: `backend/app/models/workflow.py`
  - Add `AgentTask` and `AgentStep` models, or create `backend/app/models/agent.py` if the model file becomes too broad.
- Modify: `backend/app/models/__init__.py`
  - Export any newly created model classes.
- Modify: `backend/app/api/v2/knowledge.py`
  - Add KB delete, batch add/remove, reindex, conversation list/detail, and improved QA routes.
- Modify: `backend/app/api/v2/workflow.py`
  - Keep workflow definition routes and add agent task detail/continue routes if not kept under `knowledge.py`.
- Modify: `backend/app/services/workspace_db.py`
  - Keep public service methods stable, but delegate RAG and agent internals to focused helper classes.
- Create: `backend/app/services/rag_pipeline.py`
  - Own retrieval, rerank, answer generation, conversation persistence, citation snapshots, and no-result handling.
- Create: `backend/app/services/tool_registry.py`
  - Own built-in tool definitions, JSON schema validation, and tool dispatch.
- Create: `backend/app/services/agent_executor.py`
  - Own task understanding, planning, missing-parameter prompts, retries, observations, and final answer generation.
- Modify: `backend/tests/test_workspace_api.py`
  - Add API and behavior coverage for RAG scope, batch operations, multi-turn persistence, and tool-flow execution.
- Modify: `backend/tests/test_openapi_export.py`
  - Assert new v2 paths appear in exported OpenAPI.

### Frontend Files

- Modify: `frontend/src/client/workspace.ts`
  - Add typed adapters for new RAG and agent endpoints. Import new generated SDK functions directly from `@/client/generated/sdk.gen` when Vite HMR cannot see the barrel export.
- Modify: `frontend/src/stores/knowledge.ts`
  - Make this the authoritative RAG store for KB CRUD, batch file membership, conversations, citations, and loading/error states.
- Modify: `frontend/src/stores/workflow.ts`
  - Keep workflow-definition state and add agent task state only if it remains small.
- Create: `frontend/src/stores/agent.ts`
  - Use this if agent task execution state would make `workflow.ts` too broad.
- Modify: `frontend/src/views/RagQaView.vue`
  - Replace local state and `useWorkspaceStore` usage with `useKnowledgeStore` plus focused child components.
- Create: `frontend/src/components/rag/KnowledgeBaseSidebar.vue`
- Create: `frontend/src/components/rag/KnowledgeBaseManager.vue`
- Create: `frontend/src/components/rag/KnowledgeFilePicker.vue`
- Create: `frontend/src/components/rag/KnowledgeConversationPanel.vue`
- Create: `frontend/src/components/rag/KnowledgeCitationList.vue`
- Modify: `frontend/src/views/WorkflowBuilderView.vue`
  - Remove direct `fetch()` debug calls and consume generated-client store actions.
- Create: `frontend/src/components/workflow/AgentTaskComposer.vue`
- Create: `frontend/src/components/workflow/ToolCatalogPanel.vue`
- Create: `frontend/src/components/workflow/AgentExecutionTimeline.vue`
- Create: `frontend/src/components/workflow/ToolResultViewer.vue`
- Modify: `frontend/src/stores/__tests__/workspace.spec.ts`
  - Move new RAG/agent expectations into focused tests as the old workspace store loses ownership.
- Create: `frontend/src/stores/__tests__/knowledge.spec.ts`
- Create: `frontend/src/stores/__tests__/agent.spec.ts`
- Create: `frontend/src/components/rag/__tests__/KnowledgeFilePicker.spec.ts`
- Create: `frontend/src/components/rag/__tests__/KnowledgeConversationPanel.spec.ts`
- Create: `frontend/src/components/workflow/__tests__/AgentExecutionTimeline.spec.ts`
- Modify: `frontend/src/views/__tests__/WorkspaceView.spec.ts`
  - Keep only route composition assertions that still belong to the workspace shell.

---

## Task 1: Backend Contract Tests For Scoped Knowledge Bases

**Files:**
- Modify: `backend/tests/test_workspace_api.py`
- Modify: `backend/tests/test_openapi_export.py`

- [x] **Step 1: Add failing tests for personal/team scoped KB CRUD**

Add tests that create a personal knowledge base, create a team knowledge base, update category/tags, archive it, delete it, and verify an outsider cannot read or mutate it.

Expected assertions:
- `POST /api/v2/knowledge-bases` accepts `scope_type`, `scope_id`, `category`, `tags`.
- `GET /api/v2/knowledge-bases` only returns KBs visible to the current user.
- `DELETE /api/v2/knowledge-bases/{kb_id}` returns 204 and removes it from later lists.
- Outsider requests return 403 with a structured code such as `KB_SCOPE_DENIED`.

- [x] **Step 2: Add OpenAPI path assertions**

Assert the exported schema contains:

```text
/api/v2/knowledge-bases
/api/v2/knowledge-bases/{kb_id}
/api/v2/knowledge-bases/{kb_id}/files
/api/v2/knowledge-bases/{kb_id}/files:batch-add
/api/v2/knowledge-bases/{kb_id}/files:batch-remove
/api/v2/knowledge-bases/{kb_id}/reindex
```

- [x] **Step 3: Run red tests**

Run:

```bash
cd backend
PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "knowledge_base and scope"
PYTHONPATH=. uv run python -m pytest tests/test_openapi_export.py -q
```

Expected: API behavior tests fail before implementation with missing fields/routes or unexpected 404/422.

---

## Task 2: Backend Knowledge Models And Schemas

**Files:**
- Modify: `backend/app/domain/knowledge.py`
- Modify: `backend/app/models/knowledge.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/alembic/versions/20260711_rag_agent_refactor.py`

- [x] **Step 1: Extend knowledge Pydantic schemas**

Add these concepts to `backend/app/domain/knowledge.py`:

```python
KnowledgeScopeType = Literal["personal", "team"]
KnowledgeBaseStatus = Literal["active", "archived", "deleted"]
KnowledgeFreshnessPolicy = Literal["manual", "on_file_update"]
KnowledgeIndexStatus = Literal["queued", "indexing", "indexed", "failed"]
```

Extend create/update/public schemas with:

```python
scope_type: KnowledgeScopeType = "personal"
scope_id: str | None = None
category: str | None = Field(default=None, max_length=80)
tags: list[str] = Field(default_factory=list, max_length=20)
freshness_policy: KnowledgeFreshnessPolicy = "manual"
last_indexed_at: datetime | None = None
```

- [x] **Step 2: Add batch file schemas**

Add:

```python
class KnowledgeFileBatchRequest(BaseModel):
    file_ids: list[str] = Field(min_length=1, max_length=100)

class KnowledgeFileBatchResponse(BaseModel):
    added: list[KnowledgeDocumentPublic] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    skipped: list[dict[str, str]] = Field(default_factory=list)
```

- [x] **Step 3: Add conversation schemas**

Add:

```python
class KnowledgeConversationPublic(BaseModel):
    id: str
    kb_id: str
    title: str
    message_count: int
    updated_at: datetime

class KnowledgeMessagePublic(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime
```

- [x] **Step 4: Extend SQLAlchemy models**

In `backend/app/models/knowledge.py`, add columns to `KnowledgeBase`:

```python
scope_type: Mapped[str] = mapped_column(String(16), default="personal", index=True)
scope_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
category: Mapped[str] = mapped_column(String(80), default="")
tags: Mapped[str] = mapped_column(Text, default="[]")
freshness_policy: Mapped[str] = mapped_column(String(32), default="manual")
last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

Add columns to `KnowledgeDocument`:

```python
version_sha: Mapped[str] = mapped_column(String(64), default="")
error_message: Mapped[str] = mapped_column(Text, default="")
```

Add `KnowledgeConversation`, `KnowledgeMessage`, and `KnowledgeCitationSnapshot` tables with `kb_id`, `conversation_id`, `message_id`, role/content/citation JSON fields, and timestamps.

- [x] **Step 5: Add migration**

Create `backend/alembic/versions/20260711_rag_agent_refactor.py` with upgrade/downgrade operations for the added columns and tables. Keep existing nullable/default behavior so current local databases migrate without data loss.

- [x] **Step 6: Run contract tests**

Run:

```bash
cd backend
PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "knowledge_base and scope"
```

Expected: tests still fail only at missing service behavior, not at schema import or database mapping.

---

## Task 3: Backend Knowledge APIs And Permission Enforcement

**Files:**
- Modify: `backend/app/api/v2/knowledge.py`
- Modify: `backend/app/services/workspace_db.py`

- [x] **Step 1: Add route handlers**

Add handlers for:

```text
DELETE /knowledge-bases/{kb_id}
GET /knowledge-bases/{kb_id}/files
POST /knowledge-bases/{kb_id}/files:batch-add
POST /knowledge-bases/{kb_id}/files:batch-remove
POST /knowledge-bases/{kb_id}/reindex
GET /knowledge-bases/{kb_id}/conversations
GET /conversations/{conversation_id}
```

- [x] **Step 2: Add service permission helpers**

In `WorkspaceServiceDB`, add a helper equivalent to:

```python
async def _ensure_kb_access(self, kb_id: str, user: UserPublic, action: str) -> KnowledgeBase:
    kb = await self._kbs.get_by_id(kb_id)
    if kb is None or kb.status == "deleted":
        raise WorkspaceError("KB_NOT_FOUND", "知识库不存在")
    if kb.scope_type == "personal" and kb.owner_id != user.id:
        raise WorkspaceError("KB_SCOPE_DENIED", "无权访问该个人知识库")
    if kb.scope_type == "team":
        await self._ensure_team_member(kb.scope_id or "", user)
    return kb
```

Use the existing project error type and current permission helpers instead of introducing a parallel exception format.

- [x] **Step 3: Implement batch add**

For each file id:
- Verify file read access.
- Skip if already attached to the KB.
- Parse/index file through the same durable file-content path used by reparse and download.
- Return `added` documents and `skipped` entries with codes such as `FILE_NOT_FOUND`, `FILE_NOT_READABLE`, `FILE_ALREADY_IN_KB`, `FILE_PARSE_FAILED`.

- [x] **Step 4: Implement batch remove**

For each file id or document id:
- Delete the `KnowledgeDocument` and its chunks.
- Remove KB id from file metadata.
- Clear the FAISS cache for that KB.
- Return `removed` and `skipped`.

- [x] **Step 5: Run backend tests**

Run:

```bash
cd backend
PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "knowledge_base or batch"
```

Expected: scoped KB and batch file tests pass.

---

## Task 4: RAG Pipeline Refactor And Conversation Persistence

**Files:**
- Create: `backend/app/services/rag_pipeline.py`
- Modify: `backend/app/services/workspace_db.py`
- Modify: `backend/tests/test_workspace_api.py`

- [x] **Step 1: Add failing tests for multi-turn RAG**

Add a test that:
- Creates a KB.
- Adds two indexed files.
- Asks a first question.
- Asks a follow-up question with the returned `conversation_id`.
- Verifies the second answer uses prior context.
- Verifies `GET /api/v2/conversations/{conversation_id}` returns user question, assistant answer, and citation snapshots.

- [x] **Step 2: Extract retrieval pipeline**

Move retrieval generation into `RagPipeline` with methods:

```python
class RagPipeline:
    async def retrieve(self, kb_id: str, question: str, top_k: int) -> list[Citation]: ...
    async def answer(self, kb_id: str, question: str, conversation_id: str | None, top_k: int, report_mode: bool) -> QAResponse: ...
```

Keep FAISS search and `generate_rag_answer()` behavior compatible with the current implementation.

- [x] **Step 3: Persist citation snapshots**

When an assistant message is stored, persist citation data as JSON or rows linked to the assistant message id. The UI must be able to show old citations even if the underlying file is later removed from the KB.

- [x] **Step 4: Add no-result and incomplete-index handling**

Return clear responses:
- `KB_NO_MATCH`: no relevant snippets found.
- `KB_FILE_NOT_INDEXED`: selected KB has files but no indexed chunks.
- `KB_EMPTY`: selected KB has no files.

For these cases, still store the user question and assistant response in the conversation.

- [x] **Step 5: Run backend RAG tests**

Run:

```bash
cd backend
PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "rag or qa or conversation"
PYTHONPATH=. uv run python -m pytest tests/test_embedding.py tests/test_llm.py -q
```

Expected: RAG, embedding, and LLM fallback tests pass.

---

## Task 5: Backend Tool Registry And Agent Executor

**Files:**
- Modify: `backend/app/domain/workflow.py`
- Create: `backend/app/services/tool_registry.py`
- Create: `backend/app/services/agent_executor.py`
- Modify: `backend/app/services/workspace_db.py`
- Modify: `backend/app/api/v2/knowledge.py`
- Modify: `backend/app/api/v2/workflow.py`
- Modify: `backend/tests/test_workspace_api.py`

- [x] **Step 1: Add failing tests for tool catalog**

Assert `GET /api/v2/tools` returns at least:
- `calculator`
- `course_lookup`
- `file_content_search`
- `database_query` or `python_data`

Each tool must include `name`, `description`, `input_schema`, and `output_schema`.

- [x] **Step 2: Define explicit agent phases**

Update `AgentStep` to include:

```python
phase: Literal["understand", "plan", "call", "observe", "answer"]
tool_name: str | None = None
input_json: dict[str, Any] = Field(default_factory=dict)
output_json: dict[str, Any] = Field(default_factory=dict)
status: Literal["pending", "running", "success", "failed", "needs_clarification"]
error_message: str | None = None
```

Keep a compatibility mapper for old frontend `type` if current generated clients still consume `thought/action/observation/answer`.

- [x] **Step 3: Implement `ToolRegistry`**

Register tools with deterministic implementations:
- `calculator`: evaluate arithmetic expressions through Python `ast`, allowing numeric constants and arithmetic operators only.
- `course_lookup`: search existing demo/course data or a small in-service course list by query.
- `file_content_search`: search readable file content and/or KB chunks by `query`, `file_ids`, `kb_id`.
- `python_data`: accept CSV-like file id and return simple stats such as row count, column names, numeric min/max/avg.

- [x] **Step 4: Implement missing-parameter detection**

For each selected tool, validate required input keys against its schema. If missing, return task status `needs_clarification` with a Chinese question such as `请补充要查询的课程名称。`

- [x] **Step 5: Implement executor loop**

`AgentExecutor.run()` should:
- Create an `understand` step from the natural language task.
- Create a small plan with ordered tool calls.
- Call tools with generated parameters.
- Persist `call` and `observe` steps.
- Retry one failed tool call with adjusted parameters when possible.
- Return a final answer with structured `result_view` metadata for text/table/chart display.

- [x] **Step 6: Add task detail and continuation routes**

Add:

```text
GET /api/v2/agents/tasks/{task_id}
POST /api/v2/agents/tasks/{task_id}/continue
```

The continuation route accepts user-supplied missing fields and resumes the task.

- [x] **Step 7: Run backend agent tests**

Run:

```bash
cd backend
PYTHONPATH=. uv run python -m pytest tests/test_workspace_api.py -q -k "agent or tools"
```

Expected: catalog, calculator, course lookup, file content search, missing-parameter prompt, and failed-tool behavior pass.

---

## Task 6: OpenAPI Regeneration And Frontend Client Adapters

**Files:**
- Modify: `frontend/src/client/workspace.ts`
- Generated: `frontend/src/client/openapi/workspace.openapi.json`
- Generated: `frontend/src/client/generated/*`

- [x] **Step 1: Regenerate client**

Run:

```bash
cd frontend
pnpm generate:client
```

Expected: generated SDK/types include new KB, conversation, batch file, tool, and agent task endpoints.

- [x] **Step 2: Add typed adapter functions**

In `frontend/src/client/workspace.ts`, add functions:

```ts
deleteKnowledgeBase(token, kbId)
batchAddKnowledgeFiles(token, kbId, fileIds)
batchRemoveKnowledgeFiles(token, kbId, fileIds)
reindexKnowledgeBase(token, kbId)
listKnowledgeConversations(token, kbId)
getKnowledgeConversation(token, conversationId)
listTools(token)
createAgentTask(token, payload)
getAgentTask(token, taskId)
continueAgentTask(token, taskId, payload)
```

Map frontend camelCase payloads to generated snake_case request bodies.

- [x] **Step 3: Add adapter tests through stores**

Prefer testing adapter integration through Pinia stores instead of brittle SDK call details unless an adapter has non-trivial mapping.

- [x] **Step 4: Run frontend type check**

Run:

```bash
cd frontend
pnpm type-check
```

Expected: generated type changes compile.

---

## Task 7: Frontend RAG Store And Components

**Files:**
- Modify: `frontend/src/stores/knowledge.ts`
- Modify: `frontend/src/views/RagQaView.vue`
- Create: `frontend/src/components/rag/KnowledgeBaseSidebar.vue`
- Create: `frontend/src/components/rag/KnowledgeBaseManager.vue`
- Create: `frontend/src/components/rag/KnowledgeFilePicker.vue`
- Create: `frontend/src/components/rag/KnowledgeConversationPanel.vue`
- Create: `frontend/src/components/rag/KnowledgeCitationList.vue`
- Create: `frontend/src/stores/__tests__/knowledge.spec.ts`
- Create: `frontend/src/components/rag/__tests__/KnowledgeFilePicker.spec.ts`
- Create: `frontend/src/components/rag/__tests__/KnowledgeConversationPanel.spec.ts`

- [x] **Step 1: Write store tests**

Cover:
- Load KB list.
- Create personal KB.
- Create team KB.
- Update category/tags.
- Delete KB.
- Batch add and remove files.
- Ask a question and store `conversationId`.
- Load conversation messages with citations.

- [x] **Step 2: Refactor `knowledge.ts` store**

State should include:

```ts
knowledgeBases
activeKnowledgeBaseId
documentsByKbId
conversationsByKbId
activeConversationId
messagesByConversationId
selectedFileIds
loading flags
errorMessage
```

Actions should call the new client adapters and normalize error messages into clear Chinese UI copy.

- [x] **Step 3: Build `KnowledgeBaseSidebar.vue`**

Use Naive UI list/select/filter controls. It should show scope, category, tags, document count, and index state summary. It emits select/create/edit/delete events and does not call the store directly.

- [x] **Step 4: Build `KnowledgeBaseManager.vue`**

Use `NForm`, `NInput`, `NSelect`, `NDynamicTags`, and `NRadioGroup` for scope, category, tags, freshness policy, and archive/delete actions.

- [x] **Step 5: Build `KnowledgeFilePicker.vue`**

Use `NDataTable` on desktop and grouped rows on mobile. Support checkbox selection, batch add, batch remove, and visible parse/index status chips.

- [x] **Step 6: Build `KnowledgeConversationPanel.vue`**

Render message history, question composer, answer Markdown, and loading state. Keep citations in `KnowledgeCitationList.vue`.

- [x] **Step 7: Refactor `RagQaView.vue`**

Use `useKnowledgeStore()` and compose the new components. Keep route/layout shell logic in the view and move operational UI into components.

- [x] **Step 8: Run frontend RAG tests**

Run:

```bash
cd frontend
pnpm vitest run src/stores/__tests__/knowledge.spec.ts src/components/rag/__tests__/KnowledgeFilePicker.spec.ts src/components/rag/__tests__/KnowledgeConversationPanel.spec.ts
pnpm type-check
```

Expected: RAG store and component tests pass.

---

## Task 8: Frontend Agent And Tool-Flow UI

**Files:**
- Modify: `frontend/src/stores/workflow.ts`
- Create: `frontend/src/stores/agent.ts`
- Modify: `frontend/src/views/WorkflowBuilderView.vue`
- Create: `frontend/src/components/workflow/AgentTaskComposer.vue`
- Create: `frontend/src/components/workflow/ToolCatalogPanel.vue`
- Create: `frontend/src/components/workflow/AgentExecutionTimeline.vue`
- Create: `frontend/src/components/workflow/ToolResultViewer.vue`
- Create: `frontend/src/stores/__tests__/agent.spec.ts`
- Create: `frontend/src/components/workflow/__tests__/AgentExecutionTimeline.spec.ts`

- [x] **Step 1: Write agent store tests**

Cover:
- Load tool catalog.
- Create an agent task.
- Render `needs_clarification`.
- Continue a task with missing parameters.
- Store transparent execution steps and final answer.

- [x] **Step 2: Add `agent.ts` store**

State should include:

```ts
tools
activeTask
taskHistory
executionSteps
clarificationQuestion
resultView
loading
errorMessage
```

- [x] **Step 3: Build `AgentTaskComposer.vue`**

Provide a natural-language textarea, optional KB selector, optional context file selector, submit button, and clarification input when required.

- [x] **Step 4: Build `ToolCatalogPanel.vue`**

Show registered tools grouped by category with name, description, required parameters, and enabled state.

- [x] **Step 5: Build `AgentExecutionTimeline.vue`**

Render phases:
- 理解
- 规划
- 调用
- 观察
- 回答

For tool call rows, show tool name, input parameters, status, and error message.

- [x] **Step 6: Build `ToolResultViewer.vue`**

Support:
- Text answer.
- Table result from array/object data.
- Simple chart-ready summary using Naive UI statistic blocks if the result contains numeric series.

- [x] **Step 7: Refactor `WorkflowBuilderView.vue`**

Remove direct `fetch()` calls for debug start/step. Use generated-client store actions. Keep Vue Flow builder responsibilities separate from agent task execution panels.

- [x] **Step 8: Run frontend agent tests**

Run:

```bash
cd frontend
pnpm vitest run src/stores/__tests__/agent.spec.ts src/components/workflow/__tests__/AgentExecutionTimeline.spec.ts
pnpm type-check
```

Expected: agent store and timeline tests pass.

---

## Task 9: Workspace Integration And Regression Verification

**Files:**
- Modify: `frontend/src/views/WorkspaceView.vue`
- Modify: `frontend/src/composables/useWorkspaceNavigation.ts`
- Modify: `frontend/src/stores/__tests__/workspace.spec.ts`
- Modify: `frontend/src/views/__tests__/WorkspaceView.spec.ts`
- Modify: `task_plan.md`
- Modify: `progress.md`
- Modify: `findings.md`

- [x] **Step 1: Clean old ownership**

Remove duplicated RAG/agent state ownership from `workspace.ts` only after standalone `knowledge.ts` and `agent.ts` tests pass. Keep compatibility getters if existing views still consume them during transition.

- [x] **Step 2: Verify navigation**

Ensure `/rag` and `/workflow` still use the workspace layouts and route guards.

- [x] **Step 3: Run backend full verification**

Run:

```bash
cd backend
PYTHONPATH=. uv run python -m pytest -q
```

Expected: all backend tests pass.

- [x] **Step 4: Run frontend full verification**

Run:

```bash
cd frontend
pnpm vitest run
pnpm type-check
pnpm build
```

Expected: all frontend tests, type-check, and production build pass.

- [x] **Step 5: Run hygiene checks**

Run:

```bash
python3 -m json.tool .wolf/buglog.json >/dev/null
git diff --check
```

Expected: JSON validation and whitespace check pass.

- [x] **Step 6: Update planning files**

Record completed phases, commands, and findings in:
- `task_plan.md`
- `progress.md`
- `findings.md`

---

## Acceptance Criteria

- Knowledge bases support personal/team scope, edit/delete/archive, categories, tags, and freshness metadata.
- Knowledge-base file membership supports batch add and batch remove with partial success reporting.
- RAG answers persist multi-turn context, question, answer, citations, and retrieved snippets.
- RAG retrieval applies permission filtering before citations are returned.
- RAG UI exposes knowledge-base management, batch file operations, conversations, and citations.
- Tool catalog exposes at least four runnable tools with explicit schemas.
- Agent execution records understanding, planning, tool calls, observations, and final answer.
- Agent can ask for missing input and continue after user supplies it.
- Failed tool calls return clear prompts and retry once when parameters can be adjusted.
- Frontend displays tool calls, execution steps, key outputs, tables, or simple chart summaries.
- No direct API `fetch()` remains in `WorkflowBuilderView.vue` for v2 workflow/agent behavior.
- OpenAPI client is regenerated and frontend adapters compile against generated types.
- Backend pytest, frontend Vitest, type-check, build, JSON validation, and diff whitespace checks pass.

## Execution Options

1. **Subagent-Driven**
   - Use `superpowers:subagent-driven-development`.
   - Dispatch one fresh subagent per task.
   - Review results between tasks.

2. **Inline Execution**
   - Use `superpowers:executing-plans`.
   - Execute tasks in this session with checkpoints after backend contracts, backend implementation, frontend RAG, frontend agent UI, and full verification.
