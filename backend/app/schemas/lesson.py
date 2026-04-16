from pydantic import BaseModel, ConfigDict
from typing import Optional
import datetime as dt


class LessonBase(BaseModel):
    group_id: int
    title: str
    date: dt.date
    description: Optional[str] = None
    status: str = "YANGI"
    visible_to_students: bool = True


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[dt.date] = None
    description: Optional[str] = None
    status: Optional[str] = None
    visible_to_students: Optional[bool] = None


class LessonOut(LessonBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_by: int
    created_at: dt.datetime


class LessonAttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lesson_id: int
    file_path: str
    file_name: str
    created_at: dt.datetime
