---
name: whu-intelligent-file-workspace
zh_name: "智能文件管理平台原型"
en_name: "WHU Intelligent File Workspace Prototype"
description: |
  Create or refine Open Design prototypes for the WHU intelligent file management, RAG knowledge search, agent orchestration, workflow builder, and team collaboration platform.
zh_description: "为本项目生成或优化智能文件管理、RAG 知识检索、智能体编排、工具流和团队协作相关原型。"
triggers:
  - "智能文件管理"
  - "知识库问答"
  - "RAG"
  - "Agent"
  - "工具流"
  - "团队协作"
  - "权限管理"
  - "文件管理平台"
od:
  mode: prototype
  preview:
    type: html
    entry: index.html
  example_prompt: "Create a file workspace dashboard with RAG Q&A, team files, and workflow execution status."
  example_prompt_i18n:
    zh-CN: "生成一个智能文件管理工作台，包含团队文件、RAG 问答、工具流执行状态和权限提示。"
  design_system:
    requires: true
    sections: [color, typography, components, layout, responsive]
  inputs:
    - name: screen
      type: enum
      values:
        - file_workspace
        - rag_chat
        - workflow_builder
        - agent_execution
        - team_collaboration
        - permission_admin
      default: file_workspace
    - name: audience
      type: enum
      values: [student, team_leader, team_member, admin]
      default: student
    - name: density
      type: enum
      values: [comfortable, compact]
      default: compact
  outputs:
    primary: index.html
---

# Workflow

1. Read the active `DESIGN.md` from the project root and follow it as the visual contract.
2. Read the user's prompt and map it to one or more project modules:
   - File management: folders, upload, versions, tags, sharing, search.
   - RAG knowledge search: document parsing, chunks, citations, source preview, conversations.
   - Agent orchestration: Thought/Action/Observation timeline, tool calls, retries, final answer.
   - Visual workflow builder: nodes, edges, trigger, parameter binding, execution logs.
   - Team collaboration: team files, chat, annotations, activity feed, notifications.
   - Permissions: RBAC roles, resource scope, inherited permissions, audit logs.
3. Produce a single self-contained `index.html` prototype unless the user asks to edit existing Vue code.
4. Use Chinese UI copy by default. Keep text operational and concrete.
5. Build the first viewport as a usable app surface. Do not create a marketing landing page.
6. Use dense, stable UI structures: side nav, top bar, tables, trees, tabs, split panes, drawers, timelines, and status chips.
7. Make system state visible:
   - Parse/index status for files.
   - Citation/source status for RAG answers.
   - Node status for workflows.
   - Permission scope for restricted resources.
   - Online/unread status for teams.
8. Include realistic sample data for this project:
   - Teams: 生物学实验, 软件工程课程组.
   - Files: 显微镜实验报告.pdf, 需求规格说明书.md, 小组周报.docx.
   - Tools: file_search, knowledge_qa, image_ocr, file_compare, report_generate.
   - Roles: 超级管理员, 团队管理员, 成员, 访客.
9. Keep interactions plausible in static HTML:
   - Show selected states, hover/focus styles, and visible disabled states.
   - Use small inline scripts only for tabs, drawers, node selection, or mock chat state if useful.
   - Avoid dependencies that require a build step in the artifact.
10. Self-check before finishing:
   - The prototype matches `DESIGN.md`.
   - Text does not overflow on mobile or desktop.
   - The layout is not a generic SaaS landing page.
   - All key controls are discoverable.
   - `index.html` exists and can be opened directly.

# If Editing The Vue App Instead Of Generating An Artifact

When the user explicitly asks to apply the design to this repository's Vue app:

1. Use Vue 3 Composition API with `<script setup lang="ts">`.
2. Keep route-level views as composition surfaces.
3. Prefer focused components under `frontend/src/components/`.
4. Use Pinia only for cross-route shared state; keep local UI state in components or composables.
5. Prefer Naive UI components when the project already has the dependency installed.
6. Run `pnpm --dir frontend lint`, `pnpm --dir frontend type-check`, or focused tests when practical.
