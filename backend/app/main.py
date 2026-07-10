from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import router as api_router
from app.api.v2 import router as api_router_v2
from app.domain.schemas import ErrorResponse
from app.services.workspace import WorkspaceError

# Load .env files: later files override earlier ones
_env_dir = Path(__file__).resolve().parents[1]  # backend/
for _name in (".env", ".env.deepseek", ".env.local"):
    _env_path = _env_dir / _name
    if _env_path.exists():
        load_dotenv(_env_path, override=True)

# Resolve LLM config (env file values override shell defaults)
_provider = os.environ.get("LLM_PROVIDER", "").lower()
if _provider == "deepseek":
    os.environ["LLM_API_KEY"] = os.environ.get("DEEPSEEK_API_KEY", "")
    os.environ.setdefault("LLM_BASE_URL", "https://api.deepseek.com")
elif _provider == "openai":
    os.environ["LLM_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")
    os.environ.setdefault("LLM_BASE_URL", os.environ.get("OPENAI_BASE_URL", ""))
else:
    # Auto-detect: prefer env-file keys over shell OPENAI_API_KEY
    _deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if _deepseek_key:
        os.environ["LLM_API_KEY"] = _deepseek_key
        os.environ["LLM_BASE_URL"] = "https://api.deepseek.com"
        os.environ["LLM_PROVIDER"] = "deepseek"
        os.environ.setdefault("LLM_MODEL", "deepseek-chat")
    elif os.environ.get("OPENAI_API_KEY"):
        os.environ["LLM_API_KEY"] = os.environ["OPENAI_API_KEY"]
        os.environ.setdefault("LLM_PROVIDER", "openai")

# Default model
os.environ.setdefault("LLM_MODEL", os.environ.get("LLM_MODEL", "gpt-4.1-mini"))


def create_app() -> FastAPI:
    app = FastAPI(
        title="WHU Intelligent File Workspace API",
        version="0.1.0",
        description="Report-aligned MVP API for intelligent file management and agent collaboration.",
        servers=[{"url": "/"}],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    app.include_router(api_router_v2)

    @app.on_event("startup")
    async def _startup() -> None:
        from app.core.database import init_db, async_session
        await init_db()

        # Seed default admin if no users exist
        async with async_session() as session:
            from app.repositories.user import UserRepository
            repo = UserRepository(session)
            from app.models.user import User
            existing = await repo.get_by_username("admin")
            if not existing:
                import hashlib
                admin = User(
                    username=os.environ.get("ADMIN_USER", "admin"),
                    email=os.environ.get("ADMIN_EMAIL", "admin@whucs.local"),
                    hashed_password=hashlib.sha256(
                        f"dev-workspace-secret:{os.environ.get('ADMIN_PASSWORD', 'Admin@123')}".encode()
                    ).hexdigest(),
                    display_name="系统管理员",
                    roles="admin,super_admin",
                )
                await repo.create(admin)
                await session.commit()

            # Seed workflow templates
            from app.services.workspace_db import WorkspaceServiceDB
            svc = WorkspaceServiceDB(session)
            await svc._seed_workflow_templates()

    @app.exception_handler(WorkspaceError)
    async def workspace_error_handler(_: Request, exc: WorkspaceError) -> JSONResponse:
        error = ErrorResponse(code=exc.code, message=exc.message, detail=exc.detail)
        return JSONResponse(status_code=exc.status_code, content=error.model_dump())

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def create_v2_app() -> FastAPI:
    """V2-only app for OpenAPI client generation."""
    app = FastAPI(
        title="WHU API v2",
        version="2.0.0",
        servers=[{"url": "/"}],
    )
    app.include_router(api_router_v2)
    return app


app = create_app()
