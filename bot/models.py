"""
Bot uchun model interfeyslari
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

# User model interfeysi
class User:
    def __init__(self, id: int, full_name: str, role: str, phone: str, telegram_id: Optional[int] = None):
        self.id = id
        self.full_name = full_name
        self.role = role
        self.phone = phone
        self.telegram_id = telegram_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'full_name': self.full_name,
            'role': self.role,
            'phone': self.phone,
            'telegram_id': self.telegram_id
        }

# Group model interfeysi
class Group:
    def __init__(self, id: int, name: str, schedule_time: Optional[str] = None, goal_type: Optional[str] = None):
        self.id = id
        self.name = name
        self.schedule_time = schedule_time
        self.goal_type = goal_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'schedule_time': self.schedule_time,
            'goal_type': self.goal_type
        }

# Homework model interfeysi
class Homework:
    def __init__(self, id: int, title: str, description: str, due_date: datetime, lesson_title: str):
        self.id = id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.lesson_title = lesson_title

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'lesson_title': self.lesson_title
        }

# Teacher model interfeysi
class Teacher:
    def __init__(self, id: int, full_name: str, phone: str):
        self.id = id
        self.full_name = full_name
        self.phone = phone

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'full_name': self.full_name,
            'phone': self.phone
        }

# Lesson model interfeysi
class Lesson:
    def __init__(self, id: int, title: str, date: datetime, description: str, status: str, created_by: str):
        self.id = id
        self.title = title
        self.date = date
        self.description = description
        self.status = status
        self.created_by = created_by

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'date': self.date.isoformat() if self.date else None,
            'description': self.description,
            'status': self.status,
            'created_by': self.created_by
        }


class LessonDetail:
    def __init__(
        self,
        id: int,
        title: str,
        date: datetime,
        description: Optional[str] = None,
        homework_id: Optional[int] = None,
        homework_title: Optional[str] = None,
        homework_instructions: Optional[str] = None,
        homework_due_date: Optional[datetime] = None,
    ):
        self.id = id
        self.title = title
        self.date = date
        self.description = description
        self.homework_id = homework_id
        self.homework_title = homework_title
        self.homework_instructions = homework_instructions
        self.homework_due_date = homework_due_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date.isoformat() if self.date else None,
            "description": self.description,
            "homework_id": self.homework_id,
            "homework_title": self.homework_title,
            "homework_instructions": self.homework_instructions,
            "homework_due_date": self.homework_due_date.isoformat() if self.homework_due_date else None,
        }

# HomeworkSubmission model interfeysi
class HomeworkSubmission:
    def __init__(self, id: int, homework_title: str, due_date: datetime, status: str, submitted_at: datetime, text_content: str = None):
        self.id = id
        self.homework_title = homework_title
        self.due_date = due_date
        self.status = status
        self.submitted_at = submitted_at
        self.text_content = text_content

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'homework_title': self.homework_title,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'text_content': self.text_content
        }
