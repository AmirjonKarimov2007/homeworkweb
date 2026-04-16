from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.utils.enums import AttendanceStatus


class AttendanceCreate(BaseModel):
    lesson_id: int
    student_id: int
    status: AttendanceStatus
    note: str | None = None


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lesson_id: int
    student_id: int
    status: AttendanceStatus
    note: str | None
    marked_by: int
    created_at: datetime
