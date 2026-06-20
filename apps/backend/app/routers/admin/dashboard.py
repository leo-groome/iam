"""Admin dashboard router — admin-only.

Registration line for routers/__init__.py:
    from .admin.dashboard import router as admin_dashboard_router
    api_router.include_router(admin_dashboard_router)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import admin as crud
from app.db import get_db
from app.deps import require_role
from app.models.user import User
from app.schemas.admin.dashboard import DashboardResponse

router = APIRouter(prefix="/api/v1/admin/dashboard", tags=["admin-dashboard"])

_guard = require_role("admin")


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> DashboardResponse:
    kpis = await crud.get_dashboard_kpis(db)
    return DashboardResponse(**kpis)  # type: ignore[arg-type]
