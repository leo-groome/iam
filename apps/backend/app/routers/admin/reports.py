"""Admin reports router — admin-only, CSV streaming.

Registration line for routers/__init__.py:
    from .admin.reports import router as admin_reports_router
    api_router.include_router(admin_reports_router)
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import admin as crud
from app.db import get_db
from app.deps import require_role
from app.models.user import User

router = APIRouter(prefix="/api/v1/admin/reports", tags=["admin-reports"])

_guard = require_role("admin")

ReportType = Literal["enrollments", "completions", "exam_attempts"]


@router.get("/export")
async def export_report(
    report_type: ReportType = Query(..., alias="type"),  # noqa: B008
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> StreamingResponse:
    today = date.today().isoformat()
    filename = f"{report_type}-{today}.csv"

    generators = {
        "enrollments": crud.iter_enrollments_csv,
        "completions": crud.iter_completions_csv,
        "exam_attempts": crud.iter_exam_attempts_csv,
    }

    gen_fn = generators[report_type]

    async def stream() -> AsyncGenerator[str, None]:
        async for chunk in gen_fn(db):
            yield chunk

    return StreamingResponse(
        stream(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/topic-pass-rate")
async def topic_pass_rate(
    course_id: uuid.UUID = Query(...),  # noqa: B008
    current_user: User = Depends(_guard),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[dict[str, object]]:
    return await crud.topic_pass_rate(db, course_id)
