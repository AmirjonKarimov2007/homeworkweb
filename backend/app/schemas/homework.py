from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.utils.enums import HomeworkSubmissionStatus


class HomeworkCreate(BaseModel):
    lesson_id: int
    title: str
    instructions: str | None = None
    due_date: datetime | None = None
    allow_late_submission: bool = True
    max_revision_attempts: int = 2


class HomeworkOut(HomeworkCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_by: int
    created_at: datetime


class SubmissionCreate(BaseModel):
    homework_id: int
    text: str | None = None


class SubmissionAttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    submission_id: int
    file_path: str
    file_name: str
    created_at: datetime


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    homework_id: int
    student_id: int
    status: HomeworkSubmissionStatus
    text: str | None
    submitted_at: datetime
    reviewed_by: int | None
    reviewed_at: datetime | None
    attachments: list[SubmissionAttachmentOut] | None = None


class SubmissionUpdate(BaseModel):
    status: HomeworkSubmissionStatus


class HomeworkAttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    homework_id: int
    file_path: str
    file_name: str
    created_at: datetime
