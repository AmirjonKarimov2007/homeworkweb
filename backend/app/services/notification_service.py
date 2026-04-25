from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import asyncio
import json
import urllib.request
import urllib.error
import logging
from app.models.notification import Notification
from app.models.telegram import TelegramLink
from app.core.config import settings
from app.utils.enums import NotificationChannel, NotificationStatus

logger = logging.getLogger(__name__)


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


async def _send_telegram_message(chat_id: int, text: str) -> bool:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN is not configured")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    request = urllib.request.Request(
        url=url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    def _post() -> bool:
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return 200 <= response.status < 300
        except urllib.error.URLError:
            return False

    return await asyncio.to_thread(_post)


async def send_telegram_messages_to_users(
    session: AsyncSession,
    user_ids: list[int],
    title: str,
    body: str | None = None,
) -> dict:
    if not user_ids:
        return {"target_count": 0, "sent_count": 0}

    unique_ids = list(dict.fromkeys(user_ids))
    result = await session.execute(
        select(TelegramLink.telegram_id).where(
            TelegramLink.user_id.in_(unique_ids),
            TelegramLink.telegram_id.is_not(None),
        )
    )
    telegram_ids = [row[0] for row in result.all()]
    if not telegram_ids:
        return {"target_count": 0, "sent_count": 0}

    text = title if not body else f"{title}\n\n{body}"
    sent_count = 0
    for telegram_id in telegram_ids:
        if await _send_telegram_message(int(telegram_id), text):
            sent_count += 1
    return {"target_count": len(telegram_ids), "sent_count": sent_count}
