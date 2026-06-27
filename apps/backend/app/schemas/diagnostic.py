"""Diagnostic schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class DiagnosticSummary(BaseModel):
    """Minimal identity of an active general diagnostic."""

    id: UUID
    title: str


class DiagnosticActiveOut(BaseModel):
    """Response for GET /diagnostic/active.

    `active` is null when no general diagnostic has been configured from the
    admin panel — the client then skips straight to the catalog.
    """

    active: DiagnosticSummary | None = None
