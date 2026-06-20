"""Admin routers aggregated into a single admin_router for main.py to include."""

from fastapi import APIRouter

from .courses import router as courses_router
from .dashboard import router as dashboard_router
from .modules import router as modules_router
from .questions import router as questions_router
from .reports import router as reports_router
from .students import router as students_router
from .topics import router as topics_router

admin_router = APIRouter()
admin_router.include_router(courses_router)
admin_router.include_router(modules_router)
admin_router.include_router(topics_router)
admin_router.include_router(questions_router)
admin_router.include_router(students_router)
admin_router.include_router(reports_router)
admin_router.include_router(dashboard_router)
