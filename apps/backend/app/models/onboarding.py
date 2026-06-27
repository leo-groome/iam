import uuid

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class OnboardingResponse(Base, TimestampMixin):
    """Demographic/onboarding answers captured before account creation.

    1:1 with User (UNIQUE on user_id). Structured columns power national-scale
    reporting (diócesis/parroquia/pastoral); `extra` JSONB absorbs future dynamic
    survey questions without a migration. CHECK constraints mirror the Pydantic
    enums for defense-in-depth.
    """

    __tablename__ = "onboarding_responses"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_onboarding_user"),
        CheckConstraint("sexo IN ('Hombre', 'Mujer')", name="ck_onboarding_sexo"),
        CheckConstraint(
            "edad IN ('<18', '18-25', '26-35', '36-50', '>50')", name="ck_onboarding_edad"
        ),
        CheckConstraint("entorno IN ('Rural', 'Urbana')", name="ck_onboarding_entorno"),
        CheckConstraint(
            "pastoral IN ('IAM', 'Catequesis', 'Juvenil', 'Familiar', 'Otra')",
            name="ck_onboarding_pastoral",
        ),
        Index("ix_onboarding_user", "user_id"),
        Index("ix_onboarding_diocesis", "diocesis"),
        Index("ix_onboarding_parroquia", "parroquia"),
        Index("ix_onboarding_pastoral", "pastoral"),
        Index("ix_onboarding_entorno", "entorno"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    edad: Mapped[str] = mapped_column(String(10), nullable=False)
    sexo: Mapped[str] = mapped_column(String(10), nullable=False)
    diocesis: Mapped[str] = mapped_column(String(200), nullable=False)
    ciudad: Mapped[str] = mapped_column(String(200), nullable=False)
    parroquia: Mapped[str] = mapped_column(String(200), nullable=False)
    entorno: Mapped[str] = mapped_column(String(10), nullable=False)
    pastoral: Mapped[str] = mapped_column(String(20), nullable=False)
    # JSONB on Postgres (indexable, queryable); generic JSON on SQLite for tests.
    extra: Mapped[dict[str, object]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False, default=dict, server_default="{}"
    )

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates="onboarding"
    )
