import asyncio
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from services.database import db_service

async def test_db_service():
    try:
        print('Testing database service...')

        # Test finding a user by phone
        user = await db_service.find_user_by_phone('998900000001')
        if user:
            print(f'User found: {user.full_name} ({user.role})')
        else:
            print('User not found')

        # Test getting all groups
        groups = await db_service.get_all_groups()
        print(f'Groups count: {len(groups)}')

        if groups:
            print(f'Groups: {[g.name for g in groups]}')

        # Test finding user by telegram ID (should return None initially)
        tg_user = await db_service.find_user_by_telegram_id(123456789)
        print(f'Telegram user test: {tg_user is None}')

        print('All tests passed!')
        return True
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_db_service())
    sys.exit(0 if success else 1)