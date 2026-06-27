from fastapi import APIRouter

from .auth import router as auth_router
from .catalog import router as catalog_router
from .diagnostic import router as diagnostic_router
from .learning import router as learning_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(catalog_router)
api_router.include_router(learning_router)
api_router.include_router(diagnostic_router)
