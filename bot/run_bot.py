#!/usr/bin/env python3
"""
Bot ishga tushirish skripti
"""

import asyncio
import logging
from main import main, Settings
from alembic import command

async def setup_database():
    """Database va migratsiyalarni sozlash"""
    try:
        settings = Settings()
        print(f"Database URL: {settings.DATABASE_URL}")

        # Migratsiyalarni ishga tushirish
        command.upgrade('head')
        print("Database migratsiyalari muvaffaqiyatli yakunlandi!")

    except Exception as e:
        print(f"Database sozlashda xatolik: {e}")
        raise

async def main_bot():
    """Botni ishga tushirish"""
    print("Telegram Bot ishga tushirilyapti...")

    # Database ni sozlash
    await setup_database()

    # Botni ishga tushirish
    await main()

if __name__ == "__main__":
    try:
        asyncio.run(main_bot())
    except KeyboardInterrupt:
        print("\nBot to'xtatildi!")
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        logging.error(f"Xatolik: {e}", exc_info=True)