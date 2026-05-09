import asyncio
import sys
from pathlib import Path

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.db.session import AsyncSessionLocal
from sqlalchemy import insert
from app.models.user import User, Role

async def create_user():
    """Foydalanuvchini yaratish"""
    async with AsyncSessionLocal() as session:
        # Admin user yaratish
        admin_user = {
            'phone': '+998900000001',
            'full_name': 'Admin User',
            'role': Role.ADMIN,
            'hashed_password': 'admin123',  # Hozircha shu
            'is_active': True,
            'telegram_id': None,
            'telegram_username': None,
            'telegram_is_verified': True
        }

        # Test user yaratish
        test_user = {
            'phone': '+998978920967',
            'full_name': 'Test User',
            'role': Role.STUDENT,
            'hashed_password': 'test123',  # Hozircha shu
            'is_active': True,
            'telegram_id': None,
            'telegram_username': None,
            'telegram_is_verified': True
        }

        # Admin uchun
        await session.execute(insert(User).values(admin_user))

        # Test uchun
        await session.execute(insert(User).values(test_user))

        await session.commit()
        print("Foydalanuvchilar yaratildi!")

if __name__ == "__main__":
    asyncio.run(create_user())