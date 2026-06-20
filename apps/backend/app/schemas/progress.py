from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    progress_cached: int
