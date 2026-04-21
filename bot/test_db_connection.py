import asyncio
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from services.database import db_service

async def test_database_connection():
    """Test database connection"""
    print("Database ulanishini tekshirmoqda...")

    try:
        # Test finding a user by phone
        user = await db_service.find_user_by_phone("998900000001")
        if user:
            print(f"Foydalanuvchi topildi: {user.full_name} ({user.role})")
        else:
            print("Foydalanuvchi 998900000001 bilan topilmadi (normal, chunki bu test raqam)")

        # Test getting all groups
        groups = await db_service.get_all_groups()
        print(f"Guruhlar soni: {len(groups)}")

        if groups:
            print(f"Guruhlar: {[g.name for g in groups]}")

        print("Database muvaffaqiyatli ulandi!")
        return True

    except Exception as e:
        print(f"Database bilan bog'lanishda xatolik: {e}")
        print("Iltimos, PostgreSQL server ishlayotganligini va .env faylda to'g'ri DATABASE_URL ekanligini tekshiring.")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_database_connection())
    sys.exit(0 if success else 1)