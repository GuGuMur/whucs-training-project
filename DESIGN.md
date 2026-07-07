# WHU Intelligent File Workspace

## Visual Theme & Atmosphere

Calm, academic, and operations-focused. The product is an intelligent file management and agent collaboration platform for students and teams, so the interface should feel like a serious knowledge workspace rather than a marketing site. Prioritize scannable information density, predictable navigation, visible system state, and quiet confidence.

Use Wuhan University as a contextual anchor without turning the interface into a school poster. The brand signal should come through restrained blue, ink-like typography, and precise document/workspace surfaces.

## Color Palette & Roles

- **Background:** `#F6F8FB` for the app canvas.
- **Surface:** `#FFFFFF` for tool panels, tables, modals, and document viewers.
- **Surface Muted:** `#EEF2F7` for secondary navigation, file rows on hover, and inactive toolbar groups.
- **Foreground:** `#172033` for primary text.
- **Muted Foreground:** `#5D6B82` for metadata, hints, timestamps, and secondary labels.
- **Border:** `#D8E0EA` for table dividers, cards, inputs, and panel boundaries.
- **Primary:** `#246BFE` for primary commands, active nav, selected items, and focused states.
- **Primary Soft:** `#E8F0FF` for selected rows, active tabs, and non-destructive highlighted states.
- **Success:** `#1F9D55` for completed parse/index/workflow states.
- **Warning:** `#C98600` for delayed tasks, partial parsing, and permission warnings.
- **Danger:** `#D92D20` for destructive actions and failed jobs.
- **Knowledge Accent:** `#6D5DF6` only for RAG/AI-specific indicators such as citations, embeddings, and agent steps.

Do not build a one-note blue interface. Pair blue with neutral surfaces, green/warning/danger status colors, and small purple AI accents. Avoid decorative gradients, bokeh blobs, large hero gradients, and oversized marketing composition.

## Typography Rules

- **Primary UI font:** system sans stack, `Inter`, `-apple-system`, `BlinkMacSystemFont`, `"Segoe UI"`, sans-serif.
- **Chinese fallback:** `"Noto Sans SC"`, `"PingFang SC"`, `"Microsoft YaHei"`, sans-serif.
- **Monospace:** `"JetBrains Mono"`, `"SFMono-Regular"`, ui-monospace, monospace for code, JSON schemas, tool IDs, hashes, and logs.
- **Display sizes:** reserve 28-36px only for dashboard/page titles.
- **Section headings:** 18-22px, semibold.
- **Panel/card headings:** 15-17px, semibold.
- **Body text:** 14-16px.
- **Dense metadata:** 12-13px.
- Line height should be 1.45-1.65 for body text and 1.2-1.3 for headings.
- Letter spacing should remain 0 except uppercase status chips, which may use 0.04em.

Use Chinese UI copy when generating project-facing screens unless the prompt explicitly asks for English. Keep labels concise and operational: “知识库”, “文件解析中”, “执行历史”, “权限”, “引用来源”.

## Component Stylings

- **App shell:** left sidebar for primary modules, top bar for workspace/team context, main content split into resizable work panels where useful.
- **Buttons:** 6-8px radius. Primary buttons use solid `#246BFE`; secondary buttons use white surface with border; danger actions are visually restrained until confirmation.
- **Icon buttons:** use familiar icons for file actions, search, upload, refresh, settings, run, pause, and delete. Pair icon + text only for major commands.
- **Cards/panels:** 8px radius or less, 1px border, no heavy shadow. Use panels for tools and repeated items, not nested decorative cards.
- **Tables/lists:** first-class pattern for files, versions, members, workflow executions, messages, and audit logs. Support compact row height, selection, status, and batch actions.
- **Inputs:** 6px radius, 1px border, visible focus ring using `#246BFE`.
- **Tabs/segmented controls:** use for “文件 / 知识库 / 对话 / 执行记录” style mode switching.
- **Status chips:** small, semantic, and stable width where possible. Use color sparingly.
- **AI/Agent traces:** show as ordered timeline or stepper, not as large chat bubbles when density matters.
- **Citations:** visually distinct inline badges, e.g. `[实验报告 § 3]`, with hoverable source metadata.

## Layout Principles

- Prefer dashboard/workbench layouts over landing pages.
- Keep repeated operational content in tables, split panes, trees, timelines, and compact lists.
- Use a 12-column grid for wide pages, with 24px outer page padding on desktop and 16px on tablet.
- Side navigation width: 232-280px. Top bars: 56-64px high.
- Keep fixed-format elements stable: file rows, toolbar controls, workflow nodes, counters, and status chips should not shift when content changes.
- Use whitespace to group related controls, not to create decorative emptiness.
- Document and file preview areas should have clear boundaries and useful chrome: breadcrumbs, actions, metadata, and permission state.

## Depth & Elevation

- Use borders and subtle background contrast before shadows.
- Default surface elevation is flat.
- Menus, popovers, and modals may use a small shadow: 0 8px 24px rgba(15, 23, 42, 0.10).
- Avoid glassmorphism, neumorphism, 3D decoration, gradient orbs, and floating marketing cards.

## Do's and Don'ts

- Do make the first viewport a usable workspace when asked for an app page.
- Do expose system state: parse progress, embedding status, workflow status, permission scope, and unread notifications.
- Do use dense but readable tables for operational entities.
- Do distinguish personal files, team files, knowledge bases, agent tasks, and workflows clearly.
- Do show empty states with direct next actions, such as “上传文件” or “创建知识库”.
- Do keep generated Vue code compatible with Vue 3, Vite, TypeScript, Pinia, Vue Router, and Naive UI.
- Do not create generic SaaS landing pages unless explicitly asked.
- Do not use stock-style hero illustrations or oversized decorative cards.
- Do not hide core actions behind vague “more” menus when there is room for visible controls.
- Do not use vague AI copy like “unlock productivity” in product UI; show concrete actions and states.

## Responsive Behavior

- **Desktop >= 1200px:** full workbench with sidebar, top bar, main pane, and optional right detail drawer.
- **Tablet 768-1199px:** sidebar can collapse to icon rail; detail drawer overlays content.
- **Phone < 768px:** single-column stack, bottom or top navigation, full-screen drawers for filters/details, tables become grouped rows.
- Preserve primary workflows on narrow screens: upload, search, ask question, view citations, run workflow, and respond to notifications.

## Agent Prompt Guide

When generating artifacts for this project:

1. Treat the product as a student/team knowledge-work platform, not a public marketing website.
2. Favor Vue 3 Composition API with `<script setup lang="ts">` for implementation sketches.
3. Use Naive UI-compatible interaction patterns when possible: data tables, drawers, forms, tabs, dropdowns, message/notification states, and modals.
4. Build screens around the project modules: file management, RAG knowledge search, Agent task orchestration, visual workflow builder, RBAC permissions, team chat, annotations, and activity feed.
5. Include realistic Chinese data labels and states based on the project plan.
6. Keep layouts practical for repeated daily use. If a design becomes decorative, simplify it.
7. For workflow-builder views, represent nodes and edges clearly and reserve space for execution logs and node configuration.
8. For RAG views, always include citations, source previews, and permission-aware empty/error states.
