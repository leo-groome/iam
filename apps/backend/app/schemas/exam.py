from __future__ import annotations

import uuid

from pydantic import BaseModel


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


class AnswerItem(BaseModel):
    question_id: uuid.UUID
    option_id: uuid.UUID


class ExamSubmitRequest(BaseModel):
    exam_token: str
    answers: list[AnswerItem]


class ExamResult(BaseModel):
    score: int
    passed: bool
    min_score: int
    message: str
