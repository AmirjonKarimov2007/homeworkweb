from enum import Enum


class Role(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class LeadStatus(str, Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    CONVERTED = "CONVERTED"
    LOST = "LOST"


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"


class HomeworkSubmissionStatus(str, Enum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    SUBMITTED = "SUBMITTED"
    LATE = "LATE"
    REVIEWED = "REVIEWED"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    ACCEPTED = "ACCEPTED"


class PaymentStatus(str, Enum):
    UNPAID = "UNPAID"
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    OVERDUE = "OVERDUE"


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"


class PaymentReceiptStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"


class MaterialType(str, Enum):
    PDF = "PDF"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    LINK = "LINK"
    DOCUMENT = "DOCUMENT"


class NotificationChannel(str, Enum):
    TELEGRAM = "TELEGRAM"
    WEB = "WEB"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"


class EnrollmentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
