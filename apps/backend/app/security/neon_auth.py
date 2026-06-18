"""Stack Auth (Neon Auth) JWT validation via JWKS.

Security invariants:
- JWKS is cached with 1h TTL; on signature failure we refetch ONCE (key rotation).
- JWT raw value is NEVER logged; only `sub` (hashed if needed) is safe to emit.
- Algorithm is pinned to RS256; alg:none and HS* are rejected at decode level.
- 401 messages to the client are generic; details go to structured logs only.
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

import jwt
from jwt import PyJWKClient, PyJWKClientError
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JWKS client with in-process 1-hour TTL cache (thread-safe for asyncio).
# PyJWKClient already caches by kid; we wrap it with a timestamp to force
# a periodic full-refresh independent of kid changes.
# ---------------------------------------------------------------------------

_JWKS_TTL_SECONDS = 3600  # 1 hour

_jwks_client: PyJWKClient | None = None
_jwks_loaded_at: float = 0.0


def _get_jwks_client(*, force_refresh: bool = False) -> PyJWKClient:
    """Return a PyJWKClient, refreshing the cache if TTL expired or forced."""
    global _jwks_client, _jwks_loaded_at

    now = time.monotonic()
    ttl_expired = (now - _jwks_loaded_at) > _JWKS_TTL_SECONDS

    if _jwks_client is None or ttl_expired or force_refresh:
        logger.info("Fetching JWKS from Stack Auth", extra={"url": settings.stack_jwks_url})
        _jwks_client = PyJWKClient(
            settings.stack_jwks_url,
            lifespan=_JWKS_TTL_SECONDS,
            headers={"User-Agent": "iam-backend/1.0"},
        )
        _jwks_loaded_at = now

    return _jwks_client


# ---------------------------------------------------------------------------
# Claims model — only trusted fields from the validated JWT payload.
# ---------------------------------------------------------------------------


class StackAuthClaims(BaseModel):
    """Validated, trusted claims extracted from a Stack Auth JWT."""

    sub: str  # neon_user_id — primary identifier
    email: str
    name: str | None = None  # optional; may be absent in some providers


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------

_ALLOWED_ALGORITHMS = ["RS256"]


def _log_sub(sub: str) -> str:
    """Return a safe, non-reversible representation of sub for logs."""
    return hashlib.sha256(sub.encode()).hexdigest()[:12]


async def verify_stack_token(token: str) -> StackAuthClaims:
    """Decode and validate a Stack Auth JWT.

    Raises:
        jwt.exceptions.PyJWTError subclasses → caller converts to HTTP 401.
    """
    # Fetch signing key — attempt once with cached client, retry on key mismatch.
    for attempt in range(2):
        client = _get_jwks_client(force_refresh=(attempt == 1))
        try:
            signing_key = client.get_signing_key_from_jwt(token)
            break
        except PyJWKClientError as exc:
            if attempt == 0:
                logger.warning("JWKS key lookup failed; forcing refresh", extra={"error": str(exc)})
                continue
            # Second attempt also failed — give up
            logger.error("JWKS key lookup failed after refresh", extra={"error": str(exc)})
            raise jwt.InvalidTokenError("Token signature key not found") from exc

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            signing_key.key,
            algorithms=_ALLOWED_ALGORITHMS,
            # Stack Auth issues tokens with project-scoped audience.
            # The aud claim equals the Stack project ID.
            audience=settings.stack_project_id,
            options={
                "require": ["sub", "exp", "iat", "aud"],
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_signature": True,
            },
        )
    except jwt.ExpiredSignatureError:
        logger.info("Rejected expired token")
        raise
    except jwt.InvalidTokenError as exc:
        # Log error detail internally; never surface to caller
        logger.warning("JWT validation failed", extra={"reason": str(exc)})
        raise

    sub = payload.get("sub", "")
    if not sub:
        raise jwt.InvalidTokenError("Missing sub claim")

    email = payload.get("email", "")
    if not email:
        # Stack Auth always includes email; missing = malformed token
        logger.warning("JWT missing email claim", extra={"sub_hash": _log_sub(sub)})
        raise jwt.InvalidTokenError("Missing email claim")

    logger.debug("Token validated", extra={"sub_hash": _log_sub(sub)})

    return StackAuthClaims(
        sub=sub,
        email=email,
        name=payload.get("name"),
    )
