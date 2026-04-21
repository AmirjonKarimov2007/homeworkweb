import asyncio
import sys
import logging
import os
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Fix Windows console encoding
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from bot.config import BOT_TOKEN, POLLING, WEBHOOK_URL, ADMIN_IDS, BACKEND_URL
from bot.services.database import db_service
from bot.handlers import start, homework, payments, materials, notifications, profile, help, groups, admin
from bot.jobs.notifications import admin_notification_worker
import httpx

# Setup logging with UTF-8 encoding
class UTF8StreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            if hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8')
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        UTF8StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


async def check_backend_connection():
    """Check if backend is accessible"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{BACKEND_URL}/api/health")
            if resp.status_code == 200:
                logger.info("[OK] Backend bilan muvaffaqiyatli bog'landi!")
                return True
    except Exception as e:
        logger.error(f"[ERROR] Backend bilan bog'lanib bo'lmadi: {e}")
        return False


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(groups.router)
    dp.include_router(homework.router)
    dp.include_router(payments.router)
    dp.include_router(materials.router)
    dp.include_router(notifications.router)
    dp.include_router(profile.router)
    dp.include_router(help.router)
    return dp


async def notify_admin_started(bot: Bot):
    """Send notification to admin that bot started"""
    if ADMIN_IDS:
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    "Bot ishga tushdi!\n\nBackend bilan bog'langan\nBarcha xizmatlar faol"
                )
                logger.info(f"Admin {admin_id} ga xabar yuborildi")
            except Exception as e:
                logger.error(f"Admin {admin_id} ga xabar yuborib bo'lmadi: {e}")


async def run_polling():
    logger.info("=" * 50)
    logger.info("[START] Bot polling mode boshlanmoqda...")
    logger.info(f"[CONFIG] Backend URL: {BACKEND_URL}")
    logger.info(f"[CONFIG] Admin IDs: {ADMIN_IDS}")

    # Check backend connection
    backend_ok = await check_backend_connection()
    if not backend_ok:
        logger.warning("[WARN] Backend ishlamayapti! Biroz vaqtdan keyin urinib ko'ring.")

    bot = Bot(token=BOT_TOKEN)
    dp = create_dispatcher()

    # Test bot token
    try:
        me = await bot.get_me()
        logger.info(f"[BOT] @{me.username} ({me.first_name})")
        logger.info(f"[BOT] Bot ID: {me.id}")
    except Exception as e:
        logger.error(f"[ERROR] Token noto'g'ri: {e}")
        return

    # Notify admin
    await notify_admin_started(bot)

    # Start notification worker
    worker_task = asyncio.create_task(admin_notification_worker(bot))
    logger.info("[WORKER] Notification worker ishga tushdi")

    logger.info("[POLLING] Polling boshlandi...")
    logger.info("=" * 50)

    await dp.start_polling(bot)


async def run_webhook():
    logger.info("=" * 50)
    logger.info("[START] Bot webhook mode boshlanmoqda...")
    logger.info(f"[CONFIG] Backend URL: {BACKEND_URL}")
    logger.info(f"[CONFIG] Webhook URL: {WEBHOOK_URL}")

    # Check backend connection
    backend_ok = await check_backend_connection()
    if not backend_ok:
        logger.warning("[WARN] Backend ishlamayapti!")

    bot = Bot(token=BOT_TOKEN)
    dp = create_dispatcher()

    # Test bot token
    try:
        me = await bot.get_me()
        logger.info(f"[BOT] @{me.username} ({me.first_name})")
        logger.info(f"[BOT] Bot ID: {me.id}")
    except Exception as e:
        logger.error(f"[ERROR] Token noto'g'ri: {e}")
        return

    # Notify admin
    await notify_admin_started(bot)

    # Start notification worker
    worker_task = asyncio.create_task(admin_notification_worker(bot))
    logger.info("[WORKER] Notification worker ishga tushdi")

    # Setup webhook
    app = web.Application()
    webhook_path = "/webhook"
    SimpleRequestHandler(dp, bot).register(app, path=webhook_path)
    setup_application(app, dp, bot=bot)

    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL + webhook_path)
        logger.info(f"[WEBHOOK] Webhook sozlandi: {WEBHOOK_URL}{webhook_path}")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logger.info("[WEBHOOK] Webhook server 8080 portda ishlamoqda")
    logger.info("=" * 50)

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  ARABIC CENTER BOT")
    print("=" * 50 + "\n")

    try:
        if POLLING:
            asyncio.run(run_polling())
        else:
            asyncio.run(run_webhook())
    except KeyboardInterrupt:
        logger.info("\n[STOP] Bot to'xtatildi")
    except Exception as e:
        logger.error(f"\n[ERROR] Xatolik: {e}", exc_info=True)
