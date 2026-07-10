"""Admin topic schemas."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ContentType = Literal["video", "pdf", "imagen", "texto", "audio"]


class TopicCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=60)
    content_type: ContentType
    content_body: str | None = Field(None, max_length=20000)
    media_key: str | None = None
    duration_seconds: int | None = None
    has_exam: bool = True
    exam_min_score: int = Field(70, ge=50, le=100)
    order_index: int | None = Field(None, ge=0)


class TopicUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=60)
    content_type: ContentType | None = None
    content_body: str | None = Field(None, max_length=20000)
    media_key: str | None = None
    duration_seconds: int | None = None
    has_exam: bool | None = None
    exam_min_score: int | None = Field(None, ge=50, le=100)
    order_index: int | None = Field(None, ge=0)


class TopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    module_id: uuid.UUID
    title: str
    content_type: str
    content_body: str | None
    media_key: str | None
    duration_seconds: int | None
    has_exam: bool
    exam_min_score: int
    order_index: int
    archived_at: str | None = None


from app.schemas.admin.questions import QuestionResponse  # noqa: E402


class TopicWithQuestionsResponse(TopicResponse):
    questions: list[QuestionResponse] = []


class TopicReorderBody(BaseModel):
    module_id: uuid.UUID
    order: list[uuid.UUID] = Field(..., min_length=1)
