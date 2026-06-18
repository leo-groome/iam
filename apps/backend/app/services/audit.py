"""Admin audit log service.

Every POST/PATCH/DELETE in admin/* calls log_admin_action.
The call is explicit (not middleware) to keep the payload meaningful and type-safe.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AdminAudit


async def log_admin_action(
    db: AsyncSession,
    actor_id: uuid.UUID,
    action: str,
    entity: str,
    entity_id: uuid.UUID | str,
    payload: dict[str, object],
) -> None:
    """Persist one admin audit entry.

    Args:
        db: Active async session — caller owns the transaction.
        actor_id: UUID of the admin/instructor performing the action.
        action: Verb string, e.g. "create", "update", "delete", "publish", "archive".
        entity: Table/domain name, e.g. "course", "module", "topic", "question".
        entity_id: PK of the affected row (UUID or str).
        payload: Sanitised body dict — strip secrets before passing.
    """
    entry = AdminAudit(
        actor_id=actor_id,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        payload=payload,
        created_at=datetime.now(UTC),
    )
    db.add(entry)
    # Flush so the row is visible within the same transaction if needed,
    # but we do NOT commit here — the router's transaction owns the commit.
    await db.flush()
