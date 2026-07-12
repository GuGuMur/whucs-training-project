# Frontend — 智能文件工作空间

Vue 3 前端应用，提供文件管理、知识库 RAG 问答、可视化工作流编排、Agent 工具面板、团队协作和权限审计的全功能工作台。

## 技术栈

| 类别 | 选型 |
|---|---|
| 框架 | Vue 3.5 (Composition API + `<script setup>`) |
| 语言 | TypeScript 6.0 |
| 构建 | Vite 8 + Rolldown |
| UI 组件库 | Naive UI 2.44 |
| CSS 方案 | UnoCSS 66 (Wind3 preset) |
| 状态管理 | Pinia 3 |
| 路由 | Vue Router 5 |
| HTTP 客户端 | 自动生成的 hey-api SDK（`@hey-api/openapi-ts`） |
| 图表 | ECharts 6 |
| 流程图 | @vue-flow/core |
| 图标 | @iconify/vue (MDI) + Lucide Vue |
| 国际化 | vue-i18n 11 |
| Markdown | markdown-it + highlight.js |
| 测试 | Vitest 4 + @vue/test-utils + Playwright |
| 代码质量 | ESLint 10 + oxlint + oxfmt + vue-tsc |

## 快速开始

```bash
cd frontend

# 安装依赖
pnpm install --frozen-lockfile

# 启动开发服务器
pnpm dev
# → http://localhost:5173

# 注意：需要先启动后端（参见 ../backend/README.md）
# Vite 自动将 /api 请求代理到 http://127.0.0.1:8000
```

## 常用命令

| 命令 | 说明 |
|---|---|
| `pnpm dev` | 启动 Vite 开发服务器 |
| `pnpm build` | 类型检查 + 生产构建 |
| `pnpm type-check` | 仅 TypeScript 类型检查 |
| `pnpm test:unit` | 运行 Vitest 单元测试 |
| `pnpm test:e2e` | 运行 Playwright E2E 测试 |
| `pnpm generate:client` | 从后端导出 OpenAPI + 生成 SDK |
| `pnpm lint` | ESLint + oxlint 检查并修复 |
| `pnpm format` | oxfmt 格式化 |

## 生成 API 客户端

后端 OpenAPI schema 变更后需重新生成前端 SDK：

```bash
pnpm generate:client
```

此命令执行：

1. `openapi:export` — 调用后端 `app.openapi_export` 导出 `workspace.openapi.json`
2. `openapi:generate` — `@hey-api/openapi-ts` 生成 `src/client/generated/` 下的类型和 SDK 函数

## 项目结构

```
frontend/
├── src/
│   ├── main.ts                     # Vue 应用入口
│   ├── App.vue                     # 根组件（Naive UI 配置/国际化）
│   ├── assets/                     # 全局样式
│   ├── auth/                       # 认证模块
│   │   └── workspaceAccess.ts      # Session 持久化 + Auth header 生成
│   ├── client/                     # API 客户端层
│   │   ├── generated/              # 自动生成的 SDK（勿手动编辑）
│   │   │   ├── sdk.gen.ts          # 类型安全 API 函数
│   │   │   ├── types.gen.ts        # OpenAPI 类型定义
│   │   │   └── client.gen.ts       # Fetch 客户端配置
│   │   ├── openapi/                # 后端导出的 OpenAPI JSON
│   │   └── workspace.ts            # 手写适配器（camelCase 映射 + 业务逻辑）
│   ├── components/                 # 功能组件
│   │   ├── files/                  # 文件管理（工作台/侧边栏/抽屉/上传/下拉菜单）
│   │   ├── rag/                    # RAG 知识库（管理器/对话/文件选择器）
│   │   ├── team/                   # 团队协作面板
│   │   └── workflow/               # 工作流/Agent 面板
│   ├── composables/                # 组合式函数
│   │   ├── useWorkspaceLayoutMode.ts  # 响应式布局模式
│   │   ├── useWorkspaceNavigation.ts  # 导航配置
│   │   └── useMarkdown.ts             # Markdown 渲染
│   ├── layouts/                    # 布局壳
│   │   ├── DesktopWorkspaceLayout.vue # 桌面端（侧边栏 + 内容区）
│   │   └── MobileWorkspaceLayout.vue  # 手机端（顶部导航 + 内容区）
│   ├── plugins/                    # Vue 插件
│   │   ├── index.ts                # Pinia + Router + Naive UI 安装
│   │   └── naive.ts                # Naive UI 主题覆盖
│   ├── router/                     # 路由
│   │   └── index.ts                # 路由定义 + 认证守卫
│   ├── stores/                     # Pinia 状态管理
│   │   ├── auth.ts                 # 认证状态（登录/注册/会话/个人资料）
│   │   ├── workspace.ts            # 工作空间状态（文件/文件夹/标注/通知/权限）
│   │   ├── knowledge.ts            # 知识库状态（KB CRUD/文档/RAG 对话）
│   │   ├── workflowStore.ts        # 工作流状态（定义/验证/执行）
│   │   ├── agent.ts                # Agent 状态（工具/任务/执行历史）
│   │   └── permissions.ts          # 权限规则状态
│   └── views/                      # 页面视图
│       ├── LoginView.vue           # 登录/注册
│       ├── ProfileView.vue         # 个人资料编辑
│       ├── FileManagerView.vue     # 文件管理器（主工作台）
│       ├── RagQaView.vue           # RAG 知识问答
│       ├── WorkflowBuilderView.vue # 工作流/Agent 构建器
│       ├── TeamChatView.vue        # 团队协作
│       └── PermissionAuditView.vue # 权限审计
├── tests/
│   └── frontendArchitecture.spec.ts # 架构边界测试
├── index.html                      # HTML 入口
├── vite.config.ts                  # Vite 配置（Vue/UnoCSS/代理）
├── vitest.config.ts                # Vitest 配置（jsdom）
├── uno.config.ts                   # UnoCSS 配置（主题色/快捷方式）
├── openapi-ts.config.ts            # hey-api 代码生成配置
└── package.json
```

## 架构约定

### 组件分层

```
views/           ← 路由页面，组装组件 + 调用 store actions
  └── components/  ← 功能组件，纯 props/emits，不直接调 API
       └── stores/   ← Pinia store，封装 API 调用 + 状态管理
            └── client/  ← API 适配器 + 生成 SDK
```

### 关键边界

- **组件不直接调 `fetch()`** — 所有 API 调用经 `stores/` → `client/workspace.ts` → `client/generated/`
- **`src/auth/`** 独立管理 session 持久化和 auth header
- **`layouts/`** 仅负责桌面/移动端布局壳，路由组合在 `views/`
- **自动生成的 `src/client/generated/`** 不手动编辑，由 `pnpm generate:client` 更新

### 响应式设计

- 桌面端：`DesktopWorkspaceLayout.vue`（侧边栏 + 多面板）
- 手机端：`MobileWorkspaceLayout.vue`（顶部导航 + 卡片列表/分组行）
- 布局切换：`useWorkspaceLayoutMode` composable（`window.matchMedia`）

### 测试

```bash
# 单元测试（Vitest + jsdom）
pnpm test:unit

# E2E 测试（Playwright）
pnpm test:e2e

# 架构测试
pnpm vitest run tests/frontendArchitecture.spec.ts
```

测试要求：

- 使用 `NConfigProvider` 包裹 Naive UI 组件
- Pinia 测试使用 `createTestingPinia({ createSpy: vi.fn })`
- Store 测试验证 API 调用行为，不 mock 整个 store
