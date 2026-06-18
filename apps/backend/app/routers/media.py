from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db import get_db
from app.deps import get_current_user, require_role
from app.models.course import Course, Topic
from app.models.progress import Enrollment
from app.models.user import User
from app.security.media_jwt import sign_play_token
from app.services.progress_engine import compute_topic_state
from app.services.r2 import build_key, generate_upload_url

router = APIRouter(prefix="/api/v1/media", tags=["media"])

limiter = Limiter(key_func=get_remote_address)

# ── content-type gates per scope ──────────────────────────────────────────────

_SCOPE_ALLOWED_TYPES: dict[str, frozenset[str]] = {
    "video": frozenset({"video/mp4", "video/webm"}),
    "pdf": frozenset({"application/pdf"}),
    "imagen": frozenset({"image/jpeg", "image/png", "image/webp"}),
    "cover": frozenset({"image/jpeg", "image/png", "image/webp"}),
}

_TOPIC_ACCESSIBLE_STATES = frozenset({"disponible", "contenido_visto", "aprobado", "en_repaso"})

# ── schemas ───────────────────────────────────────────────────────────────────


class UploadUrlRequest(BaseModel):
    filename: str
    content_type: str
    scope: Literal["video", "pdf", "imagen", "cover"]


class UploadUrlResponse(BaseModel):
    put_url: str
    key: str
    expires_in: int


class PlayTokenRequest(BaseModel):
    topic_id: uuid.UUID


class PlayTokenResponse(BaseModel):
    token: str
    media_url: str
    expires_in: int


# ── endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/upload-url",
    response_model=UploadUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a presigned PUT URL for R2 upload (admin/instructor only)",
)
@limiter.limit("30/minute")
async def get_upload_url(
    request: Request,
    body: UploadUrlRequest,
    current_user: User = Depends(require_role("admin", "instructor")),  # noqa: B008
) -> UploadUrlResponse:
    allowed = _SCOPE_ALLOWED_TYPES[body.scope]
    if body.content_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "invalid_content_type",
                "detail": (
                    f"content_type {body.content_type!r} is not valid for scope {body.scope!r}. "
                    f"Allowed: {sorted(allowed)}"
                ),
            },
        )

    key = await build_key(body.scope, body.filename)
    put_url = await generate_upload_url(key, body.content_type, expires_in=600)
    return UploadUrlResponse(put_url=put_url, key=key, expires_in=600)


@router.post(
    "/play-token",
    response_model=PlayTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Issue a short-lived JWT to stream a topic's media via the CF Worker",
)
async def get_play_token(
    body: PlayTokenRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> PlayTokenResponse:
    result = await db.execute(
        select(Topic).where(Topic.id == body.topic_id).options(selectinload(Topic.module))
    )
    topic = result.scalar_one_or_none()

    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    if topic.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "topic_archived", "detail": "This topic is archived."},
        )

    course_result = await db.execute(select(Course).where(Course.id == topic.module.course_id))
    course = course_result.scalar_one_or_none()
    if course is None or course.status == "archivado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "course_archived", "detail": "This course is archived."},
        )

    enrollment_result = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == topic.module.course_id,
        )
    )
    if enrollment_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "not_enrolled", "detail": "Not enrolled in this course."},
        )

    if not topic.media_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "no_media_key", "detail": "This topic has no associated media."},
        )

    state = await compute_topic_state(db, current_user, topic)

    if state not in _TOPIC_ACCESSIBLE_STATES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "topic_locked", "detail": "Access to this topic's media is not yet unlocked."},
        )

    token = sign_play_token(current_user.id, topic.media_key)
    media_url = f"{settings.r2_public_base}/{topic.media_key}"

    return PlayTokenResponse(token=token, media_url=media_url, expires_in=900)


# ── registration hint (owner adds this to app/main.py — NOT via api_router to avoid double /api/v1 prefix) ──
# from app.routers.media import router as media_router
# app.include_router(media_router)
