import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class Question(Base, TimestampMixin):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint(
            "(topic_id IS NULL) <> (module_id IS NULL)",
            name="ck_questions_xor_scope",
        ),
        Index("ix_questions_topic", "topic_id"),
        Index("ix_questions_module", "module_id"),
        Index("ix_questions_topic_order", "topic_id", "order_index"),
        Index("ix_questions_module_order", "module_id", "order_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=True
    )
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=True
    )
    enunciado: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    archived_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    topic: Mapped["Topic | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Topic", back_populates="questions", foreign_keys=[topic_id]
    )
    module: Mapped["Module | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Module", back_populates="questions", foreign_keys=[module_id]
    )
    options: Mapped[list["Option"]] = relationship(
        "Option", back_populates="question", cascade="all, delete-orphan", order_by="Option.order_index"
    )


class Option(Base):
    __tablename__ = "options"
    __table_args__ = (Index("ix_options_question", "question_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    question: Mapped["Question"] = relationship("Question", back_populates="options")
