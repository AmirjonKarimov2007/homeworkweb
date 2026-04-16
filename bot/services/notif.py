"""
Telegram notification service for sending targeted notifications
"""
from typing import List, Optional
from aiogram import Bot
from bot.services.api import api_client
from bot.utils.enums import NotificationType


class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_to_all(self, title: str, body: str, notification_type: str = "announcement") -> int:
        """Send notification to all linked users"""
        resp = await api_client.send_notification(
            sent_by=0,  # System notification
            target_type="all",
            target_id=None,
            title=title,
            body=body,
            notification_type=notification_type
        )
        return await self._send_to_telegram_ids(resp.get("telegram_ids", []), title, body)

    async def send_to_group(self, group_id: int, title: str, body: str, notification_type: str = "announcement") -> int:
        """Send notification to a specific group"""
        resp = await api_client.send_notification(
            sent_by=0,
            target_type="group",
            target_id=group_id,
            title=title,
            body=body,
            notification_type=notification_type
        )
        return await self._send_to_telegram_ids(resp.get("telegram_ids", []), title, body)

    async def send_to_user(self, user_id: int, title: str, body: str, notification_type: str = "announcement") -> int:
        """Send notification to a specific user"""
        resp = await api_client.send_notification(
            sent_by=0,
            target_type="user",
            target_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type
        )
        return await self._send_to_telegram_ids(resp.get("telegram_ids", []), title, body)

    async def send_homework_notification(
        self,
        group_id: int,
        homework_title: str,
        due_date: str,
        description: Optional[str] = None
    ) -> int:
        """Send homework assignment notification to a group"""
        title = f"📝 Yangi uy ishi: {homework_title}"
        body = f"Uy ishi berildi: {homework_title}\n"
        if description:
            body += f"\nTavsif: {description}\n"
        body += f"\n⏰ Muddati: {due_date}"
        return await self.send_to_group(group_id, title, body, NotificationType.HOMEWORK.value)

    async def send_payment_reminder(
        self,
        user_id: int,
        amount: int,
        month: str,
        group_name: str
    ) -> int:
        """Send payment reminder to a user"""
        title = "💳 To'lov eslatmasi"
        body = (
            f"E'tibor bering, {month} oyi uchun to'lov qilishingiz kerak.\n"
            f"Guruh: {group_name}\n"
            f"Summa: {amount:,} so'm\n\n"
            f"Iltimos, vaqtida to'lang."
        )
        return await self.send_to_user(user_id, title, body, NotificationType.PAYMENT.value)

    async def send_lesson_reminder(
        self,
        group_id: int,
        lesson_title: str,
        time: str
    ) -> int:
        """Send lesson reminder to a group"""
        title = f"📚 Dars boshlanmoqda: {lesson_title}"
        body = f"Dars {time} da boshlanadi.\n\nGuruh uchun tayyor bo'ling!"
        return await self.send_to_group(group_id, title, body, NotificationType.LESSON.value)

    async def _send_to_telegram_ids(self, telegram_ids: List[int], title: str, body: str) -> int:
        """Send message to list of telegram IDs"""
        sent_count = 0
        text = f"🔔 {title}\n\n{body}"
        for tg_id in telegram_ids:
            try:
                await self.bot.send_message(tg_id, text)
                sent_count += 1
            except Exception as e:
                print(f"Failed to send to {tg_id}: {e}")
        return sent_count


# Global instance (will be initialized in bot startup)
notification_service: Optional[NotificationService] = None


def init_notification_service(bot: Bot):
    global notification_service
    notification_service = NotificationService(bot)
