"""Certificate router — /api/v1/certificates.

Registration (add to app/routers/__init__.py):
    from .certificates import router as certificates_router
    api_router.include_router(certificates_router)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.deps import get_current_user
from app.models.certificate import Certificate
from app.models.course import Course
from app.models.user import User
from app.services.certificate import can_issue_certificate, issue_certificate

router = APIRouter(prefix="/certificates", tags=["certificates"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class CertificatePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_uuid: uuid.UUID
    course_title: str
    student_name: str
    issued_at: str  # ISO 8601 string; formatting done in Spanish on the verify page
    verify_url: str


def _to_public(cert: Certificate) -> CertificatePublic:
    issued_at = cast(datetime, cert.issued_at)
    return CertificatePublic(
        public_uuid=cert.public_uuid,
        course_title=cert.course_title_snapshot,
        student_name=cert.student_name_snapshot,
        issued_at=issued_at.isoformat(),
        verify_url=f"{settings.certificate_verify_base_url}/verify/{cert.public_uuid}",
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/issue/{course_id}",
    response_model=CertificatePublic,
    status_code=status.HTTP_201_CREATED,
    summary="Emit or retrieve a certificate for the authenticated user",
    description=(
        "Idempotent: returns the existing certificate if already issued. "
        "Returns 422 with code='course_incomplete' if the user has not completed the course."
    ),
)
async def issue_certificate_endpoint(
    course_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CertificatePublic:
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    eligible = await can_issue_certificate(db, current_user, course)
    if not eligible:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "course_incomplete", "detail": "Course must be 100% complete to issue a certificate."},
        )

    cert = await issue_certificate(db, current_user, course)
    await db.commit()
    await db.refresh(cert)
    return _to_public(cert)


@router.get(
    "/{public_uuid}",
    response_model=CertificatePublic,
    summary="Get certificate metadata by public UUID (auth optional)",
)
async def get_certificate(
    public_uuid: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CertificatePublic:
    result = await db.execute(
        select(Certificate).where(Certificate.public_uuid == public_uuid)
    )
    cert = result.scalar_one_or_none()
    if cert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    return _to_public(cert)


@router.patch(
    "/{public_uuid}/refresh-name",
    response_model=CertificatePublic,
    summary="Refresh student name snapshot to current user.full_name (owner only)",
    description=(
        "R-CERT-04 resolution: PRD frontend says name should reflect 'momento de descarga'. "
        "The certificate is issued with a snapshot. The frontend calls this endpoint immediately "
        "before displaying or sharing to sync the snapshot with the user's current full_name. "
        "Only the certificate owner may call this."
    ),
)
async def refresh_certificate_name(
    public_uuid: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CertificatePublic:
    result = await db.execute(
        select(Certificate).where(Certificate.public_uuid == public_uuid)
    )
    cert = result.scalar_one_or_none()
    if cert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    if cert.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this certificate",
        )

    cert.student_name_snapshot = current_user.full_name
    await db.commit()
    await db.refresh(cert)
    return _to_public(cert)
