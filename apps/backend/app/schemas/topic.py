from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class TopicProgressDetail(BaseModel):
    video_last_pos_seconds: int
    video_max_seen_pct: int
    pdf_last_page: int
    pdf_total_pages: int | None


class ContentBlockProgressView(BaseModel):
    video_last_pos_seconds: int
    video_max_seen_pct: int
    pdf_last_page: int
    pdf_total_pages: int | None
    completed: bool


class ContentBlockView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    media_key: str | None
    content_body: str | None
    duration_seconds: int | None
    order_index: int
    progress: ContentBlockProgressView


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
    blocks: list[ContentBlockView] = []


class HeartbeatRequest(BaseModel):
    type: str
    block_id: uuid.UUID | None = None
    pos_seconds: int | None = None
    duration_seconds: int | None = None
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
