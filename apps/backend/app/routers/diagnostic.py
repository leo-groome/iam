"""Diagnostic router: seam for the post-signup general diagnostic.

There is a single, admin-authored general diagnostic stored in the DB. After
account creation the client asks whether one is active and routes the new user
into it. While no diagnostic model/CRUD exists yet, this returns `active: null`
so the frontend cleanly skips it and falls back to the catalog.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.models.user import User
from app.schemas.diagnostic import DiagnosticActiveOut

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


@router.get("/active", response_model=DiagnosticActiveOut)
async def get_active_diagnostic(
    _user: User = Depends(get_current_user),  # noqa: B008
) -> DiagnosticActiveOut:
    """Return the active general diagnostic, or `active=null` when none exists.

    Placeholder until the admin-authored diagnostic model lands. The contract
    (`{"active": <diagnostic | null>}`) is stable so the frontend redirect logic
    does not change when the real diagnostic is wired in.
    """
    return DiagnosticActiveOut(active=None)
