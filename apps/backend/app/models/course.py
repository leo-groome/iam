import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class Course(Base, TimestampMixin):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('borrador', 'publicado', 'archivado')",
            name="ck_courses_status",
        ),
        Index("ix_courses_status_order", "status", "order_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    short_desc: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    long_desc: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cover_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    age_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="borrador")
    instructor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    instructor: Mapped["User | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates="courses", foreign_keys=[instructor_id]
    )
    modules: Mapped[list["Module"]] = relationship(
        "Module", back_populates="course", cascade="all, delete-orphan", order_by="Module.order_index"
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Enrollment", back_populates="course"
    )
    certificates: Mapped[list["Certificate"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Certificate", back_populates="course"
    )


class Module(Base, TimestampMixin):
    __tablename__ = "modules"
    __table_args__ = (Index("ix_modules_course_order", "course_id", "order_index"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    archived_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    course: Mapped["Course"] = relationship("Course", back_populates="modules")
    topics: Mapped[list["Topic"]] = relationship(
        "Topic", back_populates="module", cascade="all, delete-orphan", order_by="Topic.order_index"
    )
    questions: Mapped[list["Question"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Question", back_populates="module", foreign_keys="Question.module_id", order_by="Question.order_index"
    )
    exam_attempts: Mapped[list["ExamAttempt"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "ExamAttempt", back_populates="module", foreign_keys="ExamAttempt.module_id"
    )


class Topic(Base, TimestampMixin):
    __tablename__ = "topics"
    __table_args__ = (
        CheckConstraint(
            "content_type IN ('video', 'pdf', 'imagen', 'texto')",
            name="ck_topics_content_type",
        ),
        CheckConstraint("exam_min_score >= 50 AND exam_min_score <= 100", name="ck_topics_min_score"),
        Index("ix_topics_module_order", "module_id", "order_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_exam: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    exam_min_score: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    archived_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    module: Mapped["Module"] = relationship("Module", back_populates="topics")
    questions: Mapped[list["Question"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Question", back_populates="topic", foreign_keys="Question.topic_id", order_by="Question.order_index"
    )
    topic_progress: Mapped[list["TopicProgress"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "TopicProgress", back_populates="topic"
    )
    exam_attempts: Mapped[list["ExamAttempt"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "ExamAttempt", back_populates="topic", foreign_keys="ExamAttempt.topic_id"
    )
