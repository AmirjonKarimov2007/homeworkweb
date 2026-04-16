from sqlalchemy import String, Text, DateTime, func, ForeignKey, Boolean, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.utils.enums import HomeworkSubmissionStatus


class HomeworkTask(Base):
    __tablename__ = "homework_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    title: Mapped[str] = mapped_column(String(255))
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    allow_late_submission: Mapped[bool] = mapped_column(Boolean, default=True)
    max_revision_attempts: Mapped[int] = mapped_column(Integer, default=2)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    attachments = relationship("HomeworkAttachment", back_populates="homework")


class HomeworkAttachment(Base):
    __tablename__ = "homework_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homework_tasks.id"))
    file_path: Mapped[str] = mapped_column(String(255))
    file_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    homework = relationship("HomeworkTask", back_populates="attachments")


class HomeworkSubmission(Base):
    __tablename__ = "homework_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homework_tasks.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[HomeworkSubmissionStatus] = mapped_column(Enum(HomeworkSubmissionStatus), default=HomeworkSubmissionStatus.SUBMITTED)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revision_count: Mapped[int] = mapped_column(Integer, default=0)

    attachments = relationship("SubmissionAttachment", back_populates="submission")


class SubmissionAttachment(Base):
    __tablename__ = "submission_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("homework_submissions.id"))
    file_path: Mapped[str] = mapped_column(String(255))
    file_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    submission = relationship("HomeworkSubmission", back_populates="attachments")
