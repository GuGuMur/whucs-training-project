from fastapi import FastAPI

from app.routers.permissions import router as permissions_router
from app.security.middleware import PermissionMiddleware


app = FastAPI(
    title="WHU Intelligent File Workspace API",
    description="Backend API for permission management and team collaboration.",
    version="0.1.0",
)

app.add_middleware(PermissionMiddleware)
app.include_router(permissions_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
