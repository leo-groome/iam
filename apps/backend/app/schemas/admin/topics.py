"""Admin topic schemas."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


# Maps a content block's kind to the R2 upload scope prefix that app.services.r2.build_key
# generates for it ("{scope}/{uuid}/{slug}"). A media_key must live under its own kind's
# scope prefix — otherwise an instructor could point a block at media from another scope
# (e.g. "cover/...") or, more dangerously, at a specific object uploaded for a different
# course/tenant context, defeating the per-scope isolation the upload flow assumes.
_KIND_TO_SCOPE_PREFIX: dict[str, str] = {
    "video": "video/",
    "pdf": "pdf/",
    "imagen": "imagen/",
    "audio": "audio/",
}


class ContentBlockIn(BaseModel):
    kind: ContentType
    media_key: str | None = None
    content_body: str | None = Field(None, max_length=20000)
    duration_seconds: int | None = None
    order_index: int = Field(..., ge=0)

    @model_validator(mode="after")
    def _validate_kind_fields(self) -> ContentBlockIn:
        if self.kind == "texto":
            if not self.content_body or not self.content_body.strip():
                raise ValueError("content_body is required for kind='texto'")
            if self.media_key is not None:
                raise ValueError("media_key must be None for kind='texto'")
        else:
            if not self.media_key:
                raise ValueError("media_key is required for media content blocks")
            expected_prefix = _KIND_TO_SCOPE_PREFIX[self.kind]
            if not self.media_key.startswith(expected_prefix):
                raise ValueError(
                    f"media_key for kind={self.kind!r} must start with {expected_prefix!r}"
                )
        return self


class ContentBlockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    media_key: str | None
    content_body: str | None
    duration_seconds: int | None
    order_index: int


class TopicWithQuestionsResponse(TopicResponse):
    questions: list[QuestionResponse] = []
    blocks: list[ContentBlockOut] = []


class TopicReorderBody(BaseModel):
    module_id: uuid.UUID
    order: list[uuid.UUID] = Field(..., min_length=1)
