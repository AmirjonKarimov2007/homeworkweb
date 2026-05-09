from sqlalchemy import String, Boolean, Integer, DateTime, func, ForeignKey, Enum, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.utils.enums import EnrollmentStatus


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    goal_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    level_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    schedule_time: Mapped[str | None] = mapped_column(String(128), nullable=True)
    start_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    primary_teacher_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    curator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    monthly_fee: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_day: Mapped[int] = mapped_column(Integer, default=5)
    grace_days: Mapped[int] = mapped_column(Integer, default=0)
    is_payment_required: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lessons = relationship("Lesson", back_populates="group")
    course = relationship("Course", back_populates="groups")


class GroupTeacher(Base):
    __tablename__ = "group_teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StudentGroupEnrollment(Base):
    __tablename__ = "student_group_enrollments"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    monthly_fee: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[EnrollmentStatus] = mapped_column(Enum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE)
    enrolled_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
