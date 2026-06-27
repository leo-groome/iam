from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class TopicProgressDetail(BaseModel):
    video_last_pos_seconds: int
    video_max_seen_pct: int
    pdf_last_page: int
    pdf_total_pages: int | None


class TopicView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    content_type: str
    content_body: str | None
    duration_seconds: int | None
    has_exam: bool
    exam_min_score: int
    media_key: str | None
    state: str
    progress: TopicProgressDetail


class HeartbeatRequest(BaseModel):
    type: str
    pos_seconds: int | None = None
    max_seen_pct: int | None = None
    last_page: int | None = None
    total_pages: int | None = None


class HeartbeatResponse(BaseModel):
    state: str
    video_last_pos_seconds: int
    video_max_seen_pct: int
    pdf_last_page: int
    pdf_total_pages: int | None


class MarkContentDoneResponse(BaseModel):
    state: str
    content_completed_at: str | None


class TopicStateItem(BaseModel):
    id: uuid.UUID
    state: str


class ModuleProgressItem(BaseModel):
    id: uuid.UUID
    status: str
    topics: list[TopicStateItem]


class CourseProgressResponse(BaseModel):
    course_pct: int
    modules: list[ModuleProgressItem]
