"""Admin question and option schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OptionCreate(BaseModel):
    texto: str = Field(..., min_length=1, max_length=150)
    is_correct: bool = False
    order_index: int = Field(0, ge=0)


class OptionUpdate(BaseModel):
    texto: str | None = Field(None, min_length=1, max_length=150)
    is_correct: bool | None = None
    order_index: int | None = Field(None, ge=0)


class OptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    texto: str
    is_correct: bool
    order_index: int


class QuestionCreate(BaseModel):
    enunciado: str = Field(..., min_length=5, max_length=5000)
    options: list[OptionCreate] = Field(..., min_length=3, max_length=5)
    order_index: int = Field(0, ge=0)

    @model_validator(mode="after")
    def exactly_one_correct(self) -> QuestionCreate:
        correct_count = sum(1 for o in self.options if o.is_correct)
        if correct_count != 1:
            raise ValueError("Exactly one option must be marked as correct")
        return self


class QuestionUpdate(BaseModel):
    enunciado: str | None = Field(None, min_length=5, max_length=5000)


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic_id: uuid.UUID | None
    module_id: uuid.UUID | None
    enunciado: str
    order_index: int
    archived_at: str | None = None
    options: list[OptionResponse] = []
