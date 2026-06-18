"""Admin module schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class ModuleCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=60)
    description: str = Field("", max_length=2000)
    order_index: int | None = Field(None, ge=0)


class ModuleUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=60)
    description: str | None = Field(None, max_length=2000)
    order_index: int | None = Field(None, ge=0)


class ModuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    title: str
    description: str
    order_index: int
    archived_at: str | None = None


class ReorderBody(BaseModel):
    course_id: uuid.UUID
    order: list[uuid.UUID] = Field(..., min_length=1)
