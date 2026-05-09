import asyncio
import sys
from pathlib import Path

# Ensure backend root is on sys.path so `app` can be imported when running as a script
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.db.session import AsyncSessionLocal
from app.db.init import init_db
from app.core.security import hash_password
from app.utils.enums import Role
from app.models.user import User


async def seed():
    """Create only admin user if not exists"""
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if admin already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.phone == "+998917897621")
        )
        existing = result.first()

        if existing:
            print("Admin already exists")
            return

        # Create admin
        admin = User(
            full_name="Amirjon Karimov",
            phone="+998917897621",
            email="amirjon@example.com",
            role=Role.SUPER_ADMIN,
            hashed_password=hash_password("Karimoff2007"),
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print("Admin created successfully: +998917897621 / Karimoff2007")


if __name__ == "__main__":
    asyncio.run(seed())
