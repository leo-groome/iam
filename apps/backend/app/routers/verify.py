"""Public certificate verify router — /verify (no /api/v1 prefix, user-facing HTML).

Registration (add to app/main.py, NOT to api_router):
    from app.routers.verify import router as verify_router
    app.include_router(verify_router)
"""

from __future__ import annotations

import base64
import io
import uuid
from datetime import UTC

import qrcode
import qrcode.image.pil
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.certificate import Certificate

router = APIRouter(prefix="/verify", tags=["verify"])

templates = Jinja2Templates(directory="app/templates")

# Spanish month names
_MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _format_date_es(dt) -> str:  # type: ignore[no-untyped-def]
    """Format a datetime as 'DD de MMMM de YYYY' in Spanish."""
    if hasattr(dt, "tzinfo") and dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return f"{dt.day} de {_MESES_ES[dt.month - 1]} de {dt.year}"


def _generate_qr_data_uri(url: str) -> str:
    """Generate a QR code PNG and return it as a base64 data URI."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1448E0", back_color="#EEF2FF")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


@router.get(
    "/{public_uuid}",
    response_class=HTMLResponse,
    summary="Public certificate verification page (no auth, indexable)",
)
async def verify_certificate(
    public_uuid: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Response:
    result = await db.execute(
        select(Certificate).where(Certificate.public_uuid == public_uuid)
    )
    cert = result.scalar_one_or_none()
    if cert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")

    verify_url = f"{settings.certificate_verify_base_url}/verify/{cert.public_uuid}"
    qr_data_uri = _generate_qr_data_uri(verify_url)
    issued_es = _format_date_es(cert.issued_at)

    response = templates.TemplateResponse(
        request=request,
        name="verify.html",
        context={
            "student_name": cert.student_name_snapshot,
            "course_title": cert.course_title_snapshot,
            "issued_at_es": issued_es,
            "public_uuid": str(cert.public_uuid),
            "verify_url": verify_url,
            "qr_data_uri": qr_data_uri,
        },
    )
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["X-Robots-Tag"] = "index, follow"
    return response
