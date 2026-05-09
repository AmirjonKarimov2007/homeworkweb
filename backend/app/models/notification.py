from sqlalchemy import String, Text, DateTime, func, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.utils.enums import NotificationChannel, NotificationStatus


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    role_target: Mapped[str | None] = mapped_column(String(32), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), default=NotificationChannel.TELEGRAM)
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
