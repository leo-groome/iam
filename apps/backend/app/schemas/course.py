from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class CourseCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str
    short_desc: str
    cover_key: str | None
    age_min: int | None
    age_max: int | None
    order_index: int
    status: str


class CourseCardListResponse(BaseModel):
    items: list[CourseCard]
    next_cursor: str | None


class ModuleTopicItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    content_type: str
    duration_seconds: int | None
    has_exam: bool
    order_index: int


class ModuleItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    order_index: int
    topics: list[ModuleTopicItem]


class CourseDetail(BaseModel):
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
    modules: list[ModuleItem]
    enrollment_status: str
    progress_pct: int


class EnrollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    user_id: uuid.UUID
    progress_cached: int
