"""Admin course schemas — strict Pydantic v2 with PRD §5.1 limits."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TopicAdminItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    content_type: str
    has_exam: bool
    exam_min_score: int
    order_index: int
    archived_at: str | None = None


class ModuleAdminItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    order_index: int
    archived_at: str | None = None
    topics: list[TopicAdminItem] = []


class CourseAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str
    short_desc: str
    long_desc: str
    cover_key: str | None
    age_min: int | None
    age_max: int | None
    order_index: int
    status: str
    instructor_id: uuid.UUID | None
    modules: list[ModuleAdminItem] = []


class CourseAdminListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str
    short_desc: str
    status: str
    instructor_id: uuid.UUID | None
    order_index: int


class CourseCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=80)
    short_desc: str = Field(..., min_length=10, max_length=160)
    long_desc: str = Field("", max_length=2000)
    cover_key: str | None = None
    age_min: int = Field(13, ge=13, le=99)
    age_max: int = Field(99, ge=13, le=99)
    slug: str = Field(..., min_length=2, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    order_index: int = Field(0, ge=0)
    instructor_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def age_range_valid(self) -> CourseCreate:
        if self.age_max < self.age_min:
            raise ValueError("age_max must be >= age_min")
        return self


class CourseUpdate(BaseModel):
    title: str | None = Field(None, min_length=5, max_length=80)
    short_desc: str | None = Field(None, min_length=10, max_length=160)
    long_desc: str | None = Field(None, max_length=2000)
    cover_key: str | None = None
    age_min: int | None = Field(None, ge=13, le=99)
    age_max: int | None = Field(None, ge=13, le=99)
    order_index: int | None = Field(None, ge=0)
    instructor_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def age_range_valid(self) -> CourseUpdate:
        if self.age_min is not None and self.age_max is not None and self.age_max < self.age_min:
            raise ValueError("age_max must be >= age_min")
        return self


StatusLiteral = Literal["borrador", "publicado", "archivado"]
