import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from app.db.session import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select

async def test_connection():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            print('Connected to database successfully!')
            print(f'Found {len(users)} users:')
            for user in users[:5]:  # Show first 5 users
                print(f'  - {user.full_name} ({user.phone})')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    asyncio.run(test_connection())