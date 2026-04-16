import asyncio
import logging
from bot.config import ADMIN_IDS
from bot.services.api import api_client

logger = logging.getLogger(__name__)


async def admin_notification_worker(bot):
    while True:
        try:
            resp = await api_client.admin_notifications()
            if resp.get("success"):
                for note in resp.get("data", []):
                    text = f"{note['title']}\n{note.get('body','')}"
                    for admin_id in ADMIN_IDS:
                        try:
                            await bot.send_message(admin_id, text)
                        except Exception as e:
                            logger.error(f"Failed to send notification to admin {admin_id}: {e}")
                    try:
                        await api_client.mark_notification_sent(note["id"])
                    except Exception as e:
                        logger.error(f"Failed to mark notification {note['id']} as sent: {e}")
        except Exception as e:
            logger.error(f"Notification worker error: {e}")
        await asyncio.sleep(30)
