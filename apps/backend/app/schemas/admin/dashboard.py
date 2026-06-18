"""Admin dashboard KPI schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class WeeklyEnrollments(BaseModel):
    week_start: str
    count: int


class CourseCompletions(BaseModel):
    course_id: uuid.UUID
    title: str
    completions: int


class DashboardResponse(BaseModel):
    total_students: int
    new_students_last_7d: int
    active_courses: int
    completion_rate: float
    avg_exam_score: float
    stuck_students: int
    enrollments_per_week: list[WeeklyEnrollments]
    completions_per_course: list[CourseCompletions]
