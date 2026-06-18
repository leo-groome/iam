"""Auth router: /auth/sync, /me, /me/logout.

Security invariants:
- /auth/sync NEVER accepts role from client; role is always forced to 'estudiante' on create.
- Email comes exclusively from the validated JWT claims, never from request body.
- birth_date is validated server-side; no client-supplied age field is trusted.
- Rate limiting: 5/minute on /auth/sync per IP (slowapi).
"""

from __future__ import annotations

import logging
from datetime import date

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.user import SyncRequest, UserPublic
from app.security.neon_auth import verify_stack_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
me_router = APIRouter(tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


def _calculate_age(birth_date: date) -> int:
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


@router.post("/sync", response_model=UserPublic, status_code=200)
@limiter.limit("5/minute")
async def auth_sync(
    request: Request,
    body: SyncRequest,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> User:
    """Create or update a user row from a validated Stack Auth JWT + birth_date.

    Steps:
    1. Validate JWT -> extract sub, email, name.
    2. Validate age constraints server-side.
    3. Upsert user: CREATE sets role='estudiante', status='nuevo'.
       UPDATE only refreshes email + full_name (role change requires admin endpoint).
    """
    # --- 1. JWT validation ---
    token = authorization.split(" ", 1)[-1].strip() if " " in authorization else ""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        claims = await verify_stack_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    except Exception as exc:
        logger.exception("Unexpected error during token validation in /auth/sync")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    # --- 2. Age validation (server-authoritative) ---
    age = _calculate_age(body.birth_date)
    if age < 13:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "under_age", "detail": "User must be at least 13 years old."},
        )
    if age > 120:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "invalid_age", "detail": "Provided birth date results in an invalid age."},
        )

    # --- 3. Upsert ---
    email = claims.email.lower()
    result = await db.execute(select(User).where(User.neon_user_id == claims.sub))
    user = result.scalar_one_or_none()

    if user is None:
        # CREATE: role and status are hard-coded; NEVER from client.
        user = User(
            neon_user_id=claims.sub,
            email=email,  # from JWT only, normalized for case-insensitive uniqueness
            full_name=body.full_name,
            birth_date=body.birth_date,
            role="estudiante",   # enforced; client cannot set this
            status="nuevo",
        )
        db.add(user)
        logger.info("Created new user", extra={"neon_user_id_prefix": claims.sub[:8]})
    else:
        # UPDATE: only refresh mutable fields; role stays unchanged.
        changed = False
        if user.email != email:
            user.email = email
            changed = True
        if user.full_name != body.full_name:
            user.full_name = body.full_name
            changed = True
        if changed:
            logger.info("Updated user profile", extra={"neon_user_id_prefix": claims.sub[:8]})

    await db.commit()
    await db.refresh(user)
    return user


@router.get("/me", response_model=UserPublic)  # kept under /auth prefix for consistency; also mounted at /me
async def me(current_user: User = Depends(get_current_user)) -> User:  # noqa: B008
    """Return the current user's public profile."""
    return current_user


@router.post("/me/logout", status_code=204)
async def logout(current_user: User = Depends(get_current_user)) -> None:  # noqa: B008
    """Stateless logout — Stack Auth manages the session client-side."""
    # No server-side session to invalidate; 204 signals success to client.
    return None


@me_router.get("/me", response_model=UserPublic)
async def me_alias(current_user: User = Depends(get_current_user)) -> User:  # noqa: B008
    return await me(current_user)


@me_router.post("/me/logout", status_code=204)
async def logout_alias(current_user: User = Depends(get_current_user)) -> None:  # noqa: B008
    return await logout(current_user)
