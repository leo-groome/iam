import uuid

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class Enrollment(Base, TimestampMixin):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_enrollments_user_course"),
        Index("ix_enrollments_user", "user_id"),
        Index("ix_enrollments_course", "course_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    progress_cached: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship("User", back_populates="enrollments")  # type: ignore[name-defined]  # noqa: F821
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")  # type: ignore[name-defined]  # noqa: F821


class TopicProgress(Base, TimestampMixin):
    __tablename__ = "topic_progress"
    __table_args__ = (
        CheckConstraint(
            "state IN ('bloqueado', 'disponible', 'contenido_visto', 'aprobado', 'en_repaso')",
            name="ck_topic_progress_state",
        ),
        UniqueConstraint("user_id", "topic_id", name="uq_topic_progress_user_topic"),
        Index("ix_topic_progress_user_topic", "user_id", "topic_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False
    )
    state: Mapped[str] = mapped_column(nullable=False, default="bloqueado")
    video_last_pos_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    video_max_seen_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pdf_last_page: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pdf_total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="topic_progress")  # type: ignore[name-defined]  # noqa: F821
    topic: Mapped["Topic"] = relationship("Topic", back_populates="topic_progress")  # type: ignore[name-defined]  # noqa: F821


class ContentBlockProgress(Base, TimestampMixin):
    __tablename__ = "content_block_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "block_id", name="uq_content_block_progress_user_block"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    block_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_blocks.id", ondelete="CASCADE"), nullable=False
    )
    video_last_pos_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    video_max_seen_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pdf_last_page: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pdf_total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User")  # type: ignore[name-defined]  # noqa: F821
    block: Mapped["ContentBlock"] = relationship("ContentBlock")  # type: ignore[name-defined]  # noqa: F821


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"
    __table_args__ = (
        CheckConstraint(
            "(topic_id IS NULL) <> (module_id IS NULL)",
            name="ck_exam_attempts_xor_scope",
        ),
        Index("ix_exam_attempts_user_topic", "user_id", "topic_id"),
        Index("ix_exam_attempts_user_module", "user_id", "module_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=True
    )
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    min_score_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    answers: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="exam_attempts")  # type: ignore[name-defined]  # noqa: F821
    topic: Mapped["Topic | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Topic", back_populates="exam_attempts", foreign_keys=[topic_id]
    )
    module: Mapped["Module | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Module", back_populates="exam_attempts", foreign_keys=[module_id]
    )
