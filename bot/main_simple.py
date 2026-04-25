import asyncio
import logging
import os
from loguru import logger
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.dispatcher.filters import CommandStart

from database import db
from handlers import BotHandlers

# Load environment variables
load_dotenv()

# Configure logging
logger.remove()
logger.add(
    "bot.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {function}:{line} | {message}"
)

# Initialize bot and dispatcher
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def main():
    """Main bot function"""
    try:
        # Initialize database
        await db.initialize()

        # Initialize handlers
        handlers = BotHandlers(bot, dp)
        await handlers.register_handlers()

        logger.info("Bot is starting...")
        logger.info(f"Bot token: {BOT_TOKEN[:10]}...")

        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        await bot.session.close()
        await db.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise