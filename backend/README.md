# Backend — 智能文件工作空间 API

FastAPI 后端，提供文件管理、知识库 RAG、Agent 工具调用、工作流编排、团队协作和权限控制的 REST API。

## 技术栈

| 类别 | 选型 |
|---|---|
| Web 框架 | FastAPI 0.139+ |
| Python | 3.13 |
| 包管理 | uv |
| ORM | SQLAlchemy 2.0 (async) + Alembic |
| 数据库 | SQLite (开发) / MySQL + asyncmy (生产) |
| 向量检索 | FAISS (IndexFlatIP) + sentence-transformers (MiniLM-L12-v2) |
| LLM | OpenAI / DeepSeek 兼容 API，多 provider 自动降级 |
| 文档解析 | PyMuPDF (PDF) / python-docx (DOCX) / python-pptx (PPTX) / CSV / Markdown |
| 认证 | JWT (python-jose) + bcrypt 密码哈希 + refresh token rotation |
| 异步任务 | Celery + Redis / arq |
| 测试 | pytest + httpx (TestClient) |

## 快速开始

```bash
cd backend

# 安装依赖
uv sync

# 配置环境变量（可选）
cp .env.example .env.local
# 编辑 .env.local，配置 LLM_API_KEY 等

# 启动开发服务器
PYTHONPATH=. uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档自动生成：

- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

## 运行测试

```bash
# 全部测试（141 个）
PYTHONPATH=. uv run python -m pytest tests/ -v

# 跳过需要 LLM 的测试
PYTHONPATH=. uv run python -m pytest tests/ -v -k "not agent_task"

# 单个文件
PYTHONPATH=. uv run python -m pytest tests/test_parser.py -v

# 注意：DB 测试需串行运行（SQLite 不支持并行写）
```

## API 版本

| 版本 | 前缀 | 数据层 | 说明 |
|---|---|---|---|
| V1 | `/api/v1/` | 内存 | MVP 快速原型，单服务进程内状态 |
| V2 | `/api/v2/` | SQLAlchemy + SQLite | DB 持久化，文件内容 SHA-256 落盘 |

### V1 主要端点

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录（5 次失败锁定） |
| POST | `/api/v1/auth/refresh` | 刷新令牌 |
| GET | `/api/v1/users/me` | 当前用户信息 |
| PATCH | `/api/v1/users/me` | 更新个人信息 |
| GET | `/api/v1/files` | 文件列表（过滤/搜索/时间范围） |
| POST | `/api/v1/files/upload` | 文件上传 |
| GET | `/api/v1/files/{id}/download` | 文件下载 |
| DELETE | `/api/v1/files/{id}` | 软删除（回收站） |
| POST | `/api/v1/files/{id}/restore` | 从回收站恢复 |
| CRUD | `/api/v1/folders` | 文件夹树管理 |
| CRUD | `/api/v1/knowledge-bases` | 知识库管理 |
| POST | `/api/v1/qa/query` | RAG 问答 |
| CRUD | `/api/v1/workflows` | 工作流定义 |
| CRUD | `/api/v1/teams` | 团队管理 |
| CRUD | `/api/v1/permissions/rules` | ACL 权限规则 |

### V2 主要增强

- 文件内容 SHA-256 持久化存储（`backend/.data/file-contents/`）
- 文本文件在线编辑 + 版本历史
- 分片上传（multipart upload）
- 多轮 RAG 对话持久化 + 引文快照
- Agent 透明工具流（understand → plan → call → observe → answer）
- SSE 流式 Agent 执行
- WebSocket 实时推送（团队消息/通知）

## 项目结构

```
backend/
├── app/
│   ├── main.py                      # 应用工厂 + lifespan（DB 初始化、种子数据）
│   ├── openapi_export.py            # OpenAPI JSON 导出（供前端 SDK 生成）
│   ├── api/
│   │   ├── v1/                      # V1 路由（auth/files/folders/knowledge/teams/workflow/admin）
│   │   └── v2/                      # V2 路由 + WebSocket
│   ├── core/
│   │   ├── config.py                # Pydantic Settings
│   │   └── database.py              # SQLAlchemy async engine + session
│   ├── domain/                      # Pydantic 请求/响应 schema
│   ├── models/                      # SQLAlchemy ORM 模型
│   ├── repositories/                # 数据访问层
│   └── services/
│       ├── workspace.py             # V1 内存服务
│       ├── workspace_db.py          # V2 DB 持久化服务
│       ├── rag_pipeline.py          # RAG 检索引擎
│       ├── llm.py                   # LLM 多 provider 客户端
│       ├── embedding.py             # 向量嵌入服务
│       ├── parser.py                # 多格式文档解析器
│       ├── tool_registry.py         # Agent 工具注册中心（8 个内置工具）
│       ├── agent_planner.py         # LLM Agent 规划器
│       ├── agent_executor.py        # Agent 执行器（plan-call-observe 循环）
│       └── websocket_manager.py     # WebSocket 连接管理
├── tests/
│   ├── test_workspace_api.py        # API 集成测试（~100 个）
│   ├── test_parser.py               # 文档解析测试（21 个）
│   ├── test_agent_evaluation.py     # Agent 系统评估（25 个用例）
│   ├── test_llm.py                  # LLM 服务测试
│   ├── test_embedding.py            # 向量嵌入测试
│   ├── test_tool_registry.py        # 工具注册中心测试
│   └── test_openapi_export.py       # OpenAPI 导出契约测试
├── alembic/                         # 数据库迁移
├── Dockerfile                       # 多阶段 Docker 构建
├── pyproject.toml                   # 项目元数据 + 依赖
└── uv.lock                          # 锁定依赖版本
```

## Docker

```bash
# 构建
docker build -t whucs-backend -f backend/Dockerfile backend/

# 运行
docker run -p 8000:8000 \
  -e LLM_API_KEY=your-key \
  -e LLM_PROVIDER=deepseek \
  whucs-backend
```

CI 自动构建镜像并推送至 `ghcr.io/<owner>/whucs-training-project`。

## LLM 配置

支持多 provider 自动检测，优先级：`.env.deepseek` > `.env.local` > 环境变量。

```bash
# DeepSeek（性价比）
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key

# OpenAI 兼容
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_BASE_URL=https://api.openai.com/v1

# 自定义模型
LLM_MODEL=deepseek-chat
```

无 API key 时，LLM 相关功能使用模板回退（fallback）模式。
