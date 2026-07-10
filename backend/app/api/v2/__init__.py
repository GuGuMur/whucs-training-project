from fastapi import APIRouter

router = APIRouter(prefix="/api/v2")

from app.api.v2.admin import router as admin_router
from app.api.v2.auth import router as auth_router
from app.api.v2.files import router as files_router
from app.api.v2.folders import router as folders_router
from app.api.v2.general import router as general_router
from app.api.v2.knowledge import router as knowledge_router
from app.api.v2.teams import router as teams_router
from app.api.v2.workflow import router as workflow_router

router.include_router(admin_router)
router.include_router(auth_router)
router.include_router(files_router)
router.include_router(folders_router)
router.include_router(general_router)
router.include_router(knowledge_router)
router.include_router(teams_router)
router.include_router(workflow_router)
