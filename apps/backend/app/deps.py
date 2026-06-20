"""FastAPI dependency factories.

Security invariants:
- Bearer token extraction is strict: missing or malformed header -> 401 immediately.
- get_current_user never returns a partial/unsynced user; 409 forces /auth/sync.
- require_role checks the DB-persisted role, NOT a claim from the JWT.
- All 401 responses use generic messages; details are logged server-side.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import User
from app.security.neon_auth import verify_stack_token

logger = logging.getLogger(__name__)


def _extract_bearer(authorization: str) -> str:
    """Pull the token string from 'Bearer <token>'. Raises 401 on any deviation."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format")
    token = parts[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Empty bearer token")
    return token


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> User:
    """Validate Neon Auth JWT and return the corresponding DB user.

    Raises:
        401: token is missing, malformed, expired, or has invalid signature.
        409: token is valid but no user row exists -> frontend must call /auth/sync.
    """
    token = _extract_bearer(authorization)

    try:
        claims = await verify_stack_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    except Exception as exc:
        logger.exception("Unexpected error during token validation")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    result = await db.execute(select(User).where(User.neon_user_id == claims.sub))
    user = result.scalar_one_or_none()

    if user is None:
        logger.info("User not found in DB after valid token", extra={"neon_user_id_prefix": claims.sub[:8]})
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "setup_required", "detail": "User profile not found. Please complete registration."},
        )

    return user


def require_role(*allowed_roles: str) -> Callable[..., Coroutine[Any, Any, User]]:
    """Factory returning a dependency that enforces role membership.

    The role is read from the DB row, NEVER from the JWT claims.
    """
    allowed = frozenset(allowed_roles)

    async def _check(current_user: User = Depends(get_current_user)) -> User:  # noqa: B008
        if current_user.role not in allowed:
            logger.warning(
                "Role check failed",
                extra={"required": list(allowed), "actual": current_user.role},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _check


# Convenience aliases
require_admin = require_role("admin")
require_admin_or_instructor = require_role("admin", "instructor")
