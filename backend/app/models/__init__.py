from app.db.base import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.course import Course  # noqa: F401
from app.models.group import Group, GroupTeacher, StudentGroupEnrollment  # noqa: F401
from app.models.lesson import Lesson, LessonAttachment  # noqa: F401
from app.models.attendance import AttendanceRecord  # noqa: F401
from app.models.homework import HomeworkTask, HomeworkAttachment, HomeworkSubmission, SubmissionAttachment  # noqa: F401
from app.models.payment import Payment, PaymentReceipt, PaymentTransaction  # noqa: F401
from app.models.material import Material, MaterialGroupLink  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.telegram import TelegramLink  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.system_setting import SystemSetting  # noqa: F401
