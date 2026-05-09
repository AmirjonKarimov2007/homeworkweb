from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from app.utils.enums import EnrollmentStatus


class GroupBase(BaseModel):
    name: str
    goal_type: str | None = None
    level_label: str | None = None
    schedule_time: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    duration_months: int | None = None
    capacity: int | None = None
    is_active: bool = True
    primary_teacher_id: int | None = None
    curator_id: int | None = None
    course_id: int
    monthly_fee: int | None = None
    payment_day: int = 5
    grace_days: int = 0
    is_payment_required: bool = True


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: str | None = None
    goal_type: str | None = None
    level_label: str | None = None
    schedule_time: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    duration_months: int | None = None
    capacity: int | None = None
    is_active: bool | None = None
    primary_teacher_id: int | None = None
    curator_id: int | None = None
    course_id: int | None = None
    monthly_fee: int | None = None
    payment_day: int | None = None
    grace_days: int | None = None
    is_payment_required: bool | None = None


class CourseInfo(BaseModel):
    id: int
    name: str
    monthly_fee: int
    duration_months: int | None = None


class GroupOut(GroupBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
    course: CourseInfo | None = None


class EnrollmentCreate(BaseModel):
    student_id: int
    group_id: int
    monthly_fee: int | None = None


class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    group_id: int
    monthly_fee: int | None
    status: EnrollmentStatus
    enrolled_at: datetime
