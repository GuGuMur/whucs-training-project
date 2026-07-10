from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.files import router as files_router
from app.api.v1.folders import router as folders_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.teams import router as teams_router
from app.api.v1.workflow import router as workflow_router

router.include_router(auth_router)
router.include_router(files_router)
router.include_router(folders_router)
router.include_router(teams_router)
router.include_router(knowledge_router)
router.include_router(workflow_router)
router.include_router(admin_router)
