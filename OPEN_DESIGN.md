# Open Design 配置说明

本项目已按 Open Design 的项目级协议配置：

- `DESIGN.md`：项目设计系统，Open Design 会优先读取项目根目录的这个文件。
- `skills/whu-intelligent-file-workspace/SKILL.md`：项目专用 prototype skill，用于生成智能文件管理、RAG 问答、工具流、Agent 执行和团队协作相关原型。

## 使用方式

Open Design 是独立的本地设计产品/daemon，不是本 Vue 项目的 npm 依赖。官方仓库要求 Node 24 和 pnpm 10.33.x。

从官方仓库启动 Open Design：

```bash
git clone https://github.com/nexu-io/open-design.git
cd open-design
corepack enable
pnpm install
pnpm tools-dev run web
```

打开 Open Design 页面后，将本项目目录作为 folder project 导入：

```text
/home/gugumur/whucs-training-project
```

导入后 Open Design 会读取：

1. 根目录 `DESIGN.md` 作为当前项目设计系统。
2. `skills/` 目录下的项目 skill。

## Codex MCP

官方说明中，Open Design CLI 安装后可执行：

```bash
od mcp install codex
```

当前机器上的 `/usr/bin/od` 是 GNU coreutils 的 octal dump 工具，不是 Open Design CLI。因此本仓库没有直接运行该命令。安装/启动 Open Design 后，再运行上面的 MCP 命令即可把 Open Design 接入 Codex。

## 推荐 Prompt

```text
使用 whu-intelligent-file-workspace skill，生成智能文件管理工作台：左侧团队/个人空间导航，中间文件列表和知识库状态，右侧 RAG 问答与引用来源，下方显示工具流执行进度。
```

```text
生成工具流编排页面：包含 Vue Flow 风格节点画布、节点参数配置抽屉、执行历史表格、WebSocket 实时状态和失败重试提示。
```

```text
生成团队协作页面：团队文件夹、实时聊天、文件批注、成员角色和活动动态流同屏呈现。
```
