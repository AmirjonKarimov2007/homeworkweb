import asyncio
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.session import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select

async def test_simple_db():
    """Test simple database connection"""
    print("Testing simple database connection...")

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            print(f"Connected to database successfully!")
            print(f"Found {len(users)} users:")
            for user in users[:5]:
                print(f"  - {user.full_name} ({user.phone})")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_db())
    sys.exit(0 if success else 1)