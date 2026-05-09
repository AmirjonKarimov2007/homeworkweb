from pydantic import BaseModel, ConfigDict
from datetime import datetime


class CourseBase(BaseModel):
    name: str
    monthly_fee: int
    duration_months: int | None = None
    description: str | None = None
    is_active: bool = True


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    name: str | None = None
    monthly_fee: int | None = None
    duration_months: int | None = None
    description: str | None = None
    is_active: bool | None = None


class CourseOut(CourseBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
