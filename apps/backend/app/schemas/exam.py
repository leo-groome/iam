from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class OptionOut(BaseModel):
    id: uuid.UUID
    texto: str


class QuestionOut(BaseModel):
    id: uuid.UUID
    enunciado: str
    options: list[OptionOut]


class ExamResponse(BaseModel):
    exam_token: str
    questions: list[QuestionOut]
    min_score: int
    attempts_remaining: int = 3


class AnswerItem(BaseModel):
    question_id: uuid.UUID
    option_id: uuid.UUID


class ExamSubmitRequest(BaseModel):
    exam_token: str
    answers: list[AnswerItem]


class AnswerFeedback(BaseModel):
    question_id: uuid.UUID
    option_id: uuid.UUID
    enunciado: str
    texto: str
    is_correct: bool
    feedback: str


class ExamResult(BaseModel):
    score: int
    passed: bool
    min_score: int
    message: str

    attempts_remaining: int = 0
    feedback: list[AnswerFeedback] = Field(default_factory=list)
