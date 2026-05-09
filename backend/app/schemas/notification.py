from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.utils.enums import NotificationChannel, NotificationStatus


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int | None
    role_target: str | None
    title: str
    body: str | None
    channel: NotificationChannel
    status: NotificationStatus
    created_at: datetime
    sent_at: datetime | None
