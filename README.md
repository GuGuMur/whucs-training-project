# 智能文件管理与智能体协同平台

基于大模型的智能文件管理平台，集成 RAG 知识问答、可视化工作流编排、Agent 工具调用、团队协作与 RBAC 权限控制。

> 武汉大学计算机学院 · 大一小学期软工课程项目

## 技术架构

| 层        | 技术选型                             |
| --------- | ------------------------------------ |
| 前端框架  | Vue 3 (Composition API) + TypeScript |
| 构建工具  | Vite 8 + Rolldown                    |
| UI 组件库 | Naive UI                             |
| CSS 方案  | UnoCSS (Wind3)                       |
| 状态管理  | Pinia                                |
| 后端框架  | FastAPI (Python 3.13)                |
| ORM       | SQLAlchemy 2.0 + Alembic             |
| 包管理    | uv (Python) / pnpm (Node)            |
| 向量检索  | FAISS + sentence-transformers        |
| LLM       | OpenAI / DeepSeek 兼容接口           |

## 快速开始

### 前置要求

- Python ≥ 3.13
- [uv](https://docs.astral.sh/uv/)
- Node.js ≥ 22
- [pnpm](https://pnpm.io/)

### 一键启动

```bash
./setup.sh
```

启动后访问：

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- 健康检查：http://localhost:8000/health
- Swagger 文档：http://localhost:8000/docs

### 分步启动

```bash
# 后端
cd backend
uv sync
PYTHONPATH=. uv run python -m uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

## 项目结构

```
whucs-training-project/
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/           # V1 路由（auth/files/folders/knowledge/teams/workflow）
│   │   ├── api/v2/           # V2 路由（DB 持久化版本）
│   │   ├── core/             # 配置 + 数据库
│   │   ├── domain/           # Pydantic 数据模型
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── repositories/     # 数据访问层
│   │   └── services/         # 业务逻辑（workspace/RAG/LLM/embedding/parser/tools）
│   ├── tests/                # 141 个 pytest 测试
│   ├── Dockerfile            # 多阶段 Docker 构建
│   ├── pyproject.toml
│   └── README.md
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── auth/             # 认证会话管理
│   │   ├── client/           # OpenAPI 生成的 SDK + 适配器
│   │   ├── components/       # 功能组件（files/rag/team/workflow）
│   │   ├── composables/      # 组合式函数
│   │   ├── layouts/          # 桌面/移动端布局
│   │   ├── router/           # Vue Router + 路由守卫
│   │   ├── stores/           # Pinia 状态管理
│   │   └── views/            # 页面视图
│   ├── tests/                # 前端测试
│   ├── package.json
│   └── README.md
├── report/                   # 项目文档（需求/设计/实验总结）
├── .github/workflows/        # CI/CD
│   ├── ci.yml                # 自动化测试
│   └── docker-publish.yml    # Docker 镜像构建推送
├── setup.sh                  # 一键启动脚本
└── README.md
```

## CI / CD

| 工作流               | 触发条件                | 说明                                           |
| -------------------- | ----------------------- | ---------------------------------------------- |
| `ci.yml`             | push / PR to main       | 后端 pytest + 前端 type-check / vitest / build |
| `docker-publish.yml` | push to main / `v*` tag | 构建多阶段 Docker 镜像并推送至 ghcr.io         |

## 相关文档

- [后端技术文档](backend/README.md)
- [前端技术文档](frontend/README.md)
- [需求规格说明书](report/requirements/requirements_specification.md)
- [系统设计说明书](report/design/system_design_specification.md)
