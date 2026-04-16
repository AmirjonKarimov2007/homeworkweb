from enum import Enum


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class NotificationType(str, Enum):
    ANNOUNCEMENT = "announcement"
    HOMEWORK = "homework"
    PAYMENT = "payment"
    LESSON = "lesson"


class TargetType(str, Enum):
    ALL = "all"
    GROUP = "group"
    USER = "user"
