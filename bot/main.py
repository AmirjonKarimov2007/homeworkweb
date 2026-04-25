import asyncio
import logging
import os
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.dispatcher.filters import CommandStart

from database import db
from handlers import BotHandlers
from models import User

# Load environment variables
load_dotenv()

# Configure logging
logger.remove()
# Terminalga loglarni chiqarish
logger.add(
    lambda msg: print(f"\033[92m{msg}\033[0m"),  # Yashil rang
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {function}:{line} | {message}",
    colorize=True
)
# Faqat error loglarni faylga saqlash
logger.add(
    "bot.log",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {function}:{line} | {message}"
)

# Initialize bot and dispatcher
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

async def main():
    """Main bot function"""
    try:
        # Initialize database
        await db.initialize()
        logger.info("✅ Database initialized successfully")

        # Check existing users and cache them
        await cache_existing_users()
        logger.info("✅ Existing users cached")

        # Initialize handlers
        handlers = BotHandlers(bot, dp)
        await handlers.register_handlers()
        logger.info("✅ Handlers registered")

        # Admin notification
        ADMIN_ID = 1612270615
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text="🤖 Bot muvaffaqiyatli ishga tushdi!\n\n"
                     "✅ Telegram Bot API: Faol\n"
                     "✅ Database: Ulangan\n"
                     "✅ Handlerslar: Ro'yxatdan o'tkazildi\n\n"
                     f"🕐 Vaqt: {datetime.now().strftime('%H:%M:%S')}"
            )
            logger.info(f"📢 Admin {ADMIN_ID} ga xabar yuborildi")
        except Exception as e:
            logger.warning(f"⚠️ Admin {ADMIN_ID} ga xabar yuborilib bo'lmadi: {e}")

        logger.info("=" * 60)
        logger.info("🚀 BOT ISHGA TUSHDI - POLLING BOSHLANDI")
        logger.info("=" * 60)
        logger.info(f"🤖 Bot token: {BOT_TOKEN[:10]}...")

        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Error in main: {e}", exc_info=True)
        raise
    finally:
        logger.info("🛑 Bot to'xtatilmogida...")
        if bot and bot.session:
            await bot.session.close()
        await db.close()
        logger.info("✅ Database ulanish yopildi")

async def cache_existing_users():
    """Cache all existing telegram users on bot startup"""
    try:
        async with db.get_connection() as conn:
            query = """
                SELECT u.id, u.full_name, u.role, u.phone, tl.telegram_id, tl.username
                FROM users u
                JOIN telegram_links tl ON u.id = tl.user_id
                WHERE tl.telegram_id IS NOT NULL
            """
            results = await conn.fetch(query)

            for row in results:
                user = User(
                    id=row['id'],
                    full_name=row['full_name'],
                    role=row['role'],
                    phone=row['phone'],
                    telegram_id=row.get('telegram_id')
                )
                db.cache_user(user)
                logger.info(f"✅ Cached user: {user.full_name} (ID: {user.id}, Telegram: {user.telegram_id})")

            logger.info(f"✅ Total cached users: {len(results)}")
    except Exception as e:
        logger.error(f"Error caching users: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise