from sqlalchemy import DateTime, func, ForeignKey, Enum, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.utils.enums import AttendanceStatus


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus))
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    marked_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
