from __future__ import annotations

import time
import uuid

import jwt

from app.config import settings

_ALGORITHM = "HS256"
_AUDIENCE = "r2-worker"


def sign_play_token(user_id: uuid.UUID, media_key: str, ttl_seconds: int = 900) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "key": media_key,
        "aud": _AUDIENCE,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    return jwt.encode(payload, settings.media_jwt_secret, algorithm=_ALGORITHM)


def verify_play_token(token: str) -> dict[str, object]:
    """Decode and verify a play token locally. For tests only — in prod the CF Worker validates."""
    return jwt.decode(
        token,
        settings.media_jwt_secret,
        algorithms=[_ALGORITHM],
        audience=_AUDIENCE,
    )
