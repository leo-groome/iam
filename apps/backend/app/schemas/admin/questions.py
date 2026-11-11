"""Admin question and option schemas."""

from __future__ import annotations

import re
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_TAG_RE = re.compile(r"<[^>]*>")


def _check_enunciado_text(value: str | None) -> str | None:
    """El mínimo de 5 caracteres cuenta texto visible, no etiquetas HTML (`<p>a</p>` no pasa)."""
    if value is not None and len(_TAG_RE.sub("", value).replace("&nbsp;", " ").strip()) < 5:
        raise ValueError("El enunciado necesita al menos 5 caracteres de texto")
    return value


class OptionCreate(BaseModel):
    texto: str = Field(..., min_length=1, max_length=150)
    feedback: str = Field("", max_length=5000)
    is_correct: bool = False
    order_index: int = Field(0, ge=0)


class OptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    texto: str
    feedback: str
    is_correct: bool
    order_index: int


class QuestionCreate(BaseModel):
    enunciado: str = Field(..., min_length=5, max_length=5000)
    options: list[OptionCreate] = Field(..., min_length=3, max_length=5)
    order_index: int = Field(0, ge=0)

    _enunciado_text = field_validator("enunciado")(_check_enunciado_text)

    @model_validator(mode="after")
    def exactly_one_correct(self) -> QuestionCreate:
        correct_count = sum(1 for o in self.options if o.is_correct)
        if correct_count != 1:
            raise ValueError("Exactly one option must be marked as correct")
        return self


class OptionEdit(OptionCreate):
    id: uuid.UUID | None = None


class QuestionBulkItem(BaseModel):
    """Item del guardado masivo: con `id` se actualiza la pregunta existente (conserva su ID)."""

    id: uuid.UUID | None = None
    enunciado: str = Field(..., min_length=5, max_length=5000)
    options: list[OptionEdit] = Field(..., min_length=3, max_length=5)
    order_index: int = Field(0, ge=0)

    _enunciado_text = field_validator("enunciado")(_check_enunciado_text)

    @model_validator(mode="after")
    def valid_options(self) -> QuestionBulkItem:
        if sum(o.is_correct for o in self.options) != 1:
            raise ValueError("Exactly one option must be marked as correct")
        ids = [o.id for o in self.options if o.id is not None]
        if len(ids) != len(set(ids)):
            raise ValueError("Option IDs must be unique")
        return self


class QuestionUpdate(BaseModel):
    enunciado: str | None = Field(None, min_length=5, max_length=5000)
    options: list[OptionEdit] | None = Field(None, min_length=3, max_length=5)

    _enunciado_text = field_validator("enunciado")(_check_enunciado_text)

    @model_validator(mode="after")
    def valid_options(self) -> QuestionUpdate:
        if self.options is not None:
            if sum(o.is_correct for o in self.options) != 1:
                raise ValueError("Exactly one option must be marked as correct")
            ids = [o.id for o in self.options if o.id is not None]
            if len(ids) != len(set(ids)):
                raise ValueError("Option IDs must be unique")
        return self


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic_id: uuid.UUID | None
    module_id: uuid.UUID | None
    enunciado: str
    order_index: int
    archived_at: str | None = None
    options: list[OptionResponse] = []
