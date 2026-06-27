"""User-facing Pydantic schemas.

Security invariants:
- `role` is NEVER accepted from client input; set by server only.
- `birth_date` validation is server-authoritative; no client-supplied `age` field.
- `full_name` pattern blocks SQL/HTML injection characters at the schema level.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

# Allow ASCII + Latin-1 + Latin Extended-A/B letters, spaces, hyphens,
# apostrophes and periods (e.g. "José-Luis", "D'Angelo", "J. Smith").
_FULL_NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿĀ-ɏ\s\-'.]+$")


class OnboardingIn(BaseModel):
    """Demographic onboarding answers, bundled into POST /auth/sync.

    `nombre` is intentionally absent — it duplicates `full_name` and is only used
    to pre-fill the signup form on the client, never persisted here. Enums are
    enforced with `Literal` (422 on unknown values) and mirrored by DB CHECKs.
    """

    edad: Literal["<18", "18-25", "26-35", "36-50", ">50"]
    sexo: Literal["Hombre", "Mujer"]
    diocesis: str = Field(..., min_length=1, max_length=200)
    ciudad: str = Field(..., min_length=1, max_length=200)
    parroquia: str = Field(..., min_length=1, max_length=200)
    entorno: Literal["Rural", "Urbana"]
    pastoral: Literal["IAM", "Catequesis", "Juvenil", "Familiar", "Otra"]
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("diocesis", "ciudad", "parroquia")
    @classmethod
    def normalize_text(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("field cannot be blank")
        return v

    @field_validator("extra")
    @classmethod
    def cap_extra_size(cls, v: dict[str, Any]) -> dict[str, Any]:
        if len(json.dumps(v)) > 2000:
            raise ValueError("extra payload too large")
        return v


class SyncRequest(BaseModel):
    """Body for POST /auth/sync.

    `role` and `email` are intentionally absent — they come from the JWT only.
    """

    full_name: str = Field(..., min_length=3, max_length=80)
    birth_date: date
    onboarding: OnboardingIn | None = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not _FULL_NAME_PATTERN.match(v):
            raise ValueError("full_name must contain only letters and spaces")
        if len(v) < 3:
            raise ValueError("full_name must be at least 3 characters after stripping")
        return v

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("birth_date cannot be in the future")
        return v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class UserPublic(BaseModel):
    """Safe public representation of a user — no sensitive internals exposed."""

    model_config = {"from_attributes": True}

    id: UUID
    email: str
    full_name: str
    role: str
    status: str
    created_at: datetime
