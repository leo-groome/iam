"""Admin student schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StudentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    status: str
    created_at: datetime
    is_stuck: bool = False


class StudentListResponse(BaseModel):
    items: list[StudentListItem]
    total: int
    page: int
    page_size: int


class ExamAttemptSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic_id: uuid.UUID | None
    module_id: uuid.UUID | None
    score: int
    passed: bool
    min_score_snapshot: int
    created_at: datetime


class TopicProgressSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    topic_id: uuid.UUID
    state: str
    video_max_seen_pct: int
    content_completed_at: datetime | None


class EnrollmentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    started_at: datetime
    completed_at: datetime | None
    progress_cached: int


class StudentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    status: str
    created_at: datetime
    enrollments: list[EnrollmentSummary] = []
    topic_progress: list[TopicProgressSummary] = []
    exam_attempts: list[ExamAttemptSummary] = []
