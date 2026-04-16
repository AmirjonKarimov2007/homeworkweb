from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.models.notification import Notification
from app.utils.enums import NotificationChannel, NotificationStatus


async def create_notification(
    session: AsyncSession,
    title: str,
    body: str | None = None,
    user_id: int | None = None,
    role_target: str | None = None,
    channel: NotificationChannel = NotificationChannel.TELEGRAM,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        role_target=role_target,
        title=title,
        body=body,
        channel=channel,
        status=NotificationStatus.PENDING,
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return notification


async def create_notifications_bulk(
    session: AsyncSession,
    user_ids: list[int],
    title: str,
    body: str | None = None,
    channel: NotificationChannel = NotificationChannel.WEB,
) -> int:
    if not user_ids:
        return 0
    unique_ids = list(dict.fromkeys(user_ids))
    notifications = [
        Notification(
            user_id=uid,
            title=title,
            body=body,
            channel=channel,
            status=NotificationStatus.PENDING,
        )
        for uid in unique_ids
    ]
    session.add_all(notifications)
    await session.commit()
    return len(notifications)


async def mark_sent(session: AsyncSession, notification: Notification) -> Notification:
    notification.status = NotificationStatus.SENT
    notification.sent_at = datetime.utcnow()
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return notification
